// SPDX-License-Identifier: AGPL-3.0-or-later
//! Time-aware, lexical caption segmentation, independent of Whisper's BPE tokens.
//! Used for short spoken phrases and one-word-at-a-time karaoke pop.
#[derive(Clone, Debug, PartialEq)]
pub struct Word {
    pub text: String,
    pub start: f64,
    pub end: f64,
}

/// Recover **every visible word** in the transcript. Whisper word timestamp
/// tokens are best-effort, and might omit spaces, punctuation, or whole words.
/// Use them only when the entire word sequence agrees with the transcript.
pub fn split(text: &str, start: f64, end: f64, timed: Vec<Word>) -> Vec<Word> {
    if !start.is_finite() || !end.is_finite() || end <= start {
        return Vec::new();
    }
    let words: Vec<&str> = text.split_whitespace().collect();
    if words.is_empty() {
        return Vec::new();
    }
    let reliable = timed.len() == words.len()
        && timed.iter().zip(&words).all(|(t, s)| {
            t.text.trim() == *s
                && t.start.is_finite() && t.end.is_finite()
                && t.start >= start && t.end <= end && t.end > t.start
        })
        && timed.windows(2).all(|pair| pair[0].end <= pair[1].start);
    if reliable {
        return timed;
    }
    // Fallback only: proportional durations cannot be presented as accurate
    // alignment. Even with broken token timestamps, never merge a paragraph
    // into a single karaoke clip.
    let total = words.iter().map(|w| w.chars().count().max(1)).sum::<usize>() as f64;
    let mut consumed = 0usize;
    words.into_iter().map(|word| {
        let a = start + (end - start) * (consumed as f64 / total);
        consumed += word.chars().count().max(1);
        let b = start + (end - start) * (consumed as f64 / total);
        Word { text: word.to_owned(), start: a, end: b }
    }).collect()
}

/// Split speech into short phrases, preserving the original ordering and
/// silences. Enforce both character and word bounds, including in transcripts
/// without punctuation. Do not split a single lexical word mid-word.
pub fn phrases(text: &str, start: f64, end: f64, timed: Vec<Word>,
               max_chars: usize, max_words: usize) -> Vec<Word> {
    let words = split(text, start, end, timed);
    let mut result = Vec::new();
    let mut current = String::new();
    let mut first = 0.0;
    let mut last = 0.0;
    let mut count = 0usize;
    let mut prev_ends_sentence = false;
    for w in words {
        let incoming = w.text.chars().count();
        let should_break = count > 0 && (
            count >= max_words.max(1) ||
            current.chars().count() + incoming + 1 > max_chars.max(1) ||
            w.start - last >= 0.48 ||
            prev_ends_sentence ||
            w.text.starts_with('¿') || w.text.starts_with('¡')
        );
        if should_break {
            result.push(Word { text: std::mem::take(&mut current), start: first, end: last });
            count = 0;
        }
        if count == 0 { first = w.start; } else { current.push(' '); }
        current.push_str(&w.text);
        last = w.end;
        count += 1;
        prev_ends_sentence = w.text.ends_with(&['.', '?', '!', '。', '？', '！'][..]);
    }
    if count > 0 {
        result.push(Word { text: current, start: first, end: last });
    }
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    fn w(text: &str, start: f64, end: f64) -> Word {
        Word { text: text.to_owned(), start, end }
    }

    #[test]
    fn karaoke_never_keeps_a_paragraph_from_bad_whisper_tokens() {
        let text = "La Navidad tiene su encanto para toda la familia";
        let bad = vec![w(text, 0.0, 4.0)];
        let words = split(text, 0.0, 4.0, bad);
        assert_eq!(words.len(), 9);
        assert!(words.iter().all(|w| w.text.split_whitespace().count() == 1));
        assert_eq!(words.first().unwrap().start, 0.0);
        assert!((words.last().unwrap().end - 4.0).abs() < 1e-9);
    }

    #[test]
    fn valid_word_timing_survives_exactly() {
        let words = vec![w("Hola", 1.0, 1.14), w("mundo", 1.6, 2.0)];
        assert_eq!(split("Hola mundo", 1.0, 2.0, words.clone()), words);
    }

    #[test]
    fn phrases_limit_long_whisper_segments_without_punctuation() {
        let text = "Un mensaje de esperanza para cada persona que escucha este canto hoy";
        let cues = phrases(text, 0.0, 8.0, vec![], 28, 5);
        assert!(cues.len() >= 3);
        assert!(cues.iter().all(|c| c.text.split_whitespace().count() <= 5));
        assert!(cues.iter().all(|c| c.text.chars().count() <= 28));
        assert!(cues.windows(2).all(|pair| pair[0].end <= pair[1].start));
    }

    #[test]
    fn phrases_split_at_questions_without_merging_dialogue() {
        let parts = phrases("Iglesia para Dios. ¿Cuál es la pregunta?", 0.0, 4.0, vec![], 52, 12);
        assert_eq!(parts.len(), 2);
        assert_eq!(parts[0].text, "Iglesia para Dios.");
        assert_eq!(parts[1].text, "¿Cuál es la pregunta?");
    }

    #[test]
    fn empty_and_invalid_times_do_not_create_titles() {
        assert!(split(" hola", f64::NAN, 2.0, vec![]).is_empty());
        assert!(split("  ", 0.0, 2.0, vec![]).is_empty());
        assert!(phrases("X", 2.0, 0.0, vec![], 40, 8).is_empty());
    }
}
