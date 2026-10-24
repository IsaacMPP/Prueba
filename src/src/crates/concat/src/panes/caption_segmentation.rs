// SPDX-License-Identifier: AGPL-3.0-or-later
//! Readability rules for generated subtitles. These are **not** word-alignment
//! timestamps: Whisper reports phrase windows, and a subdivision estimates
//! its share of that window by the relative length of the text.
//!
//! The source transcript and the native subtitle clips share these same
//! sub-phrase IDs so a later text correction targets exactly one caption.

#[derive(Clone, Copy, Debug)]
pub struct CaptionRules {
    /// 0 = single line, 1 = two lines, 2 = one word at a time.
    pub layout: u8,
    pub chars_per_line: usize,
    pub words_per_caption: usize,
    pub min_seconds: f64,
    pub max_seconds: f64,
    pub gap_frames: u32,
}

impl Default for CaptionRules {
    fn default() -> Self {
        Self {
            layout: 1,
            chars_per_line: 42,
            words_per_caption: 12,
            min_seconds: 0.7,
            max_seconds: 6.0,
            gap_frames: 0,
        }
    }
}

impl CaptionRules {
    fn max_lines(self) -> usize {
        if self.layout == 1 { 2 } else { 1 }
    }

    fn max_words(self) -> usize {
        if self.layout == 2 { 1 } else { self.words_per_caption.clamp(1, 40) }
    }
}

/// A generated caption with estimated boundaries *inside* one Whisper phrase.
#[derive(Clone, Debug, PartialEq)]
pub struct TimedCaption {
    pub text: String,
    pub start: f64,
    pub end: f64,
}

fn lines_for(words: &[&str], limit: usize) -> Vec<String> {
    let mut lines: Vec<String> = Vec::new();
    for word in words {
        if let Some(last) = lines.last_mut() {
            if last.chars().count() + 1 + word.chars().count() <= limit {
                last.push(' ');
                last.push_str(word);
                continue;
            }
        }
        // A single exceptionally long word is kept intact, never truncated
        // or silently replaced with a different spoken word.
        lines.push((*word).to_owned());
    }
    lines
}

fn weight(words: &[&str]) -> usize {
    words.iter().map(|w| w.chars().count() + 1).sum()
}

fn fits(words: &[&str], rules: CaptionRules, seconds_per_char: f64) -> bool {
    words.len() <= rules.max_words()
        && lines_for(words, rules.chars_per_line).len() <= rules.max_lines()
        && (weight(words) as f64 * seconds_per_char <= rules.max_seconds + 1e-8)
}

pub fn voice_captions(text: &str, start: f64, end: f64, rules: CaptionRules, fps: f64) -> Vec<TimedCaption> {
    if !start.is_finite() || !end.is_finite() || end <= start {
        return Vec::new();
    }
    let words: Vec<&str> = text.split_whitespace().collect();
    if words.is_empty() { return Vec::new(); }
    let duration = end - start;
    let total_weight = weight(&words).max(1);
    let seconds_per_char = duration / total_weight as f64;
    let mut groups: Vec<Vec<&str>> = Vec::new();
    let mut current: Vec<&str> = Vec::new();

    for word in words {
        let mut candidate = current.clone();
        candidate.push(word);
        if !current.is_empty() && !fits(&candidate, rules, seconds_per_char) {
            groups.push(std::mem::take(&mut current));
        }
        current.push(word);
    }
    if !current.is_empty() { groups.push(current); }

    // Do not create a very short final cue when it can be merged into the
    // preceding one without breaking the configured readability limits.
    let mut index = groups.len();
    while index > 1 {
        index -= 1;
        if weight(&groups[index]) as f64 * seconds_per_char >= rules.min_seconds { continue; }
        let mut merged = groups[index - 1].clone();
        merged.extend_from_slice(&groups[index]);
        if fits(&merged, rules, seconds_per_char) {
            groups[index - 1] = merged;
            groups.remove(index);
        }
    }

    let mut consumed = 0usize;
    let last = groups.len();
    let gap = if fps.is_finite() && fps > 0.0 {
        rules.gap_frames as f64 / fps
    } else { 0.0 };

    groups.into_iter().enumerate().map(|(index, group)| {
        let cue_start = start + duration * consumed as f64 / total_weight as f64;
        consumed += weight(&group);
        let natural_end = if index + 1 == last {
            end
        } else {
            start + duration * consumed as f64 / total_weight as f64
        };
        // Keep a minimum visible interval if the requested gap is larger
        // than the allocated window; never extend past the source phrase.
        let cue_end = if index + 1 == last {
            natural_end
        } else {
            natural_end - gap.min((natural_end - cue_start) * 0.5)
        };
        TimedCaption {
            text: lines_for(&group, rules.chars_per_line).join("\n"),
            start: cue_start,
            end: cue_end,
        }
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn long_whisper_phrase_becomes_readable_cues_without_lost_words() {
        let source = "En la primera página está tu ayer, decisiones, personas, momentos que todavía te hacen sonreír y otros que quizá preferirías olvidar.";
        let rules = CaptionRules::default();
        let cues = voice_captions(source, 3.0, 15.0, rules, 30.0);
        assert!(cues.len() >= 3, "long phrases must actually split");
        assert_eq!(
            cues.iter().flat_map(|c| c.text.split_whitespace()).collect::<Vec<_>>(),
            source.split_whitespace().collect::<Vec<_>>()
        );
        assert!(cues.iter().all(|c| c.text.lines().count() <= 2));
        assert!(cues.iter().all(|c| c.text.lines().all(|l| l.chars().count() <= 42)));
        assert!(cues.iter().all(|c| c.end > c.start && c.start >= 3.0 && c.end <= 15.0));
        assert!(cues.windows(2).all(|p| p[0].end <= p[1].start));
    }

    #[test]
    fn one_word_mode_and_frame_gap_preserve_order_and_clock() {
        let rules = CaptionRules { layout: 2, gap_frames: 3, ..CaptionRules::default() };
        let cues = voice_captions("Hola cómo estás hoy", 2.0, 6.0, rules, 30.0);
        assert_eq!(cues.iter().map(|c| c.text.as_str()).collect::<Vec<_>>(),
            ["Hola", "cómo", "estás", "hoy"]);
        assert!((cues.first().unwrap().start - 2.0).abs() < 1e-8);
        assert!((cues.last().unwrap().end - 6.0).abs() < 1e-8);
        assert!(cues.windows(2).all(|pair| pair[1].start - pair[0].end > 0.09));
    }

    #[test]
    fn empty_and_invalid_windows_are_rejected_without_phantom_clips() {
        let rules = CaptionRules::default();
        assert!(voice_captions(" ", 0.0, 3.0, rules, 30.0).is_empty());
        assert!(voice_captions("hi", 3.0, 3.0, rules, 30.0).is_empty());
        assert!(voice_captions("hi", f64::NAN, 3.0, rules, 30.0).is_empty());
    }

    #[test]
    fn minimum_duration_merges_last_cue_only_when_limits_allow() {
        let rules = CaptionRules { chars_per_line: 20, max_seconds: 10.0, min_seconds: 3.0, ..CaptionRules::default() };
        let cues = voice_captions("one two three four five", 0.0, 4.0, rules, 30.0);
        assert_eq!(cues.iter().flat_map(|c| c.text.split_whitespace()).collect::<Vec<_>>(),
            ["one", "two", "three", "four", "five"]);
        assert!(cues.iter().all(|c| c.end <= 4.0));
    }

    #[test]
    fn very_long_words_are_never_silently_truncated() {
        let source = "hiperextraordinariamente impecable";
        let cues = voice_captions(source, 0.0, 5.0,
            CaptionRules { chars_per_line: 12, layout: 0, ..CaptionRules::default() }, 24.0);
        assert_eq!(cues.iter().flat_map(|c| c.text.split_whitespace()).collect::<Vec<_>>(),
            source.split_whitespace().collect::<Vec<_>>());
    }
}
