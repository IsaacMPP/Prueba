#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Apply Estudio Joven's caption enhancements to the pinned Concat checkout.

Runs AFTER patches/text-motion.patch. Each replacement is asserted so a change
in upstream source cannot silently create a broken/partial integration.
"""
from pathlib import Path


def replace(path: str, before: str, after: str) -> None:
    file = Path(path)
    original = file.read_text(encoding="utf-8")
    count = original.count(before)
    if count != 1:
        raise RuntimeError(f"{path}: expected one anchor, found {count}: {before[:90]!r}")
    file.write_text(original.replace(before, after, 1), encoding="utf-8")


SPEECH = "src/crates/concat-speech/src/transcribe.rs"
CAP = "src/crates/concat/src/panes/captions.rs"
DIALOG = "src/crates/concat/ui/dialogs/captions.slint"
APP = "src/crates/concat/ui/app.slint"
LIB = "src/crates/concat/src/lib.rs"

# Word timing is optional: usual captions incur no extra token alignment.
replace(SPEECH,
    "    pub text: String,\n}\n\n/// What to transcribe.",
    """    pub text: String,
    /// Estimated Whisper token timing grouped into words when requested.
    #[serde(default)]
    pub words: Vec<WordTiming>,
}

/// One timed word (seconds relative to the audio window).
#[derive(Serialize, Clone, Debug, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct WordTiming {
    pub start: f64,
    pub end: f64,
    pub text: String,
}

/// What to transcribe.""")
replace(SPEECH,
    "    pub model_id: String,\n}\n\nstruct LoadedModel",
    """    pub model_id: String,
    /// Enable Whisper's experimental token timestamps for word karaoke.
    #[serde(default)]
    pub word_timestamps: bool,
}

struct LoadedModel""")
replace(SPEECH,
    "        params.set_n_threads(threads as i32);\n",
    """        params.set_n_threads(threads as i32);
        params.set_token_timestamps(request.word_timestamps);
        params.set_split_on_word(request.word_timestamps);
""")
replace(SPEECH,
    "                keep_segment(start, end, text)\n",
    """                let mut kept = keep_segment(start, end, text)?;
                if request.word_timestamps {
                    kept.words = token_words(&segment, start, end);
                }
                Some(kept)
""")
replace(SPEECH,
    "    (end > start).then_some(Segment { start, end, text })\n",
    "    (end > start).then_some(Segment { start, end, text, words: Vec::new() })\n")
replace(SPEECH,
    "#[cfg(test)]\nmod tests {",
    """/// Compose Whisper subword tokens into words, retaining their real token
/// timestamps when available. A token can contain punctuation or several
/// whitespace-delimited words; these cases are handled without panicking.
fn token_words(segment: &whisper_rs::WhisperSegment<'_>, lower: f64, upper: f64) -> Vec<WordTiming> {
    let mut words: Vec<WordTiming> = Vec::new();
    for index in 0..segment.n_tokens() {
        let Some(token) = segment.get_token(index) else { continue };
        let Ok(piece) = token.to_str_lossy() else { continue };
        let data = token.token_data();
        if data.t0 < 0 || data.t1 <= data.t0 { continue; }
        let start = (data.t0 as f64 / 100.0).clamp(lower, upper);
        let end = (data.t1 as f64 / 100.0).clamp(lower, upper);
        if end <= start { continue; }
        let parts: Vec<&str> = piece.split_whitespace().collect();
        if parts.is_empty() { continue; }
        for (at, part) in parts.iter().enumerate() {
            let n = parts.len() as f64;
            let wstart = start + (end - start) * at as f64 / n;
            let wend = start + (end - start) * (at + 1) as f64 / n;
            if at == 0 && !piece.starts_with(char::is_whitespace) && !words.is_empty() {
                // BPE continuation or punctuation without an intervening space.
                let last = words.last_mut().expect("checked");
                last.text.push_str(part);
                last.end = last.end.max(wend);
            } else {
                words.push(WordTiming { start: wstart, end: wend, text: (*part).to_owned() });
            }
        }
    }
    words.retain(|w| !w.text.trim().is_empty() && w.end > w.start);
    words
}

#[cfg(test)]
mod tests {""")
replace(SPEECH,
    '            model_id: "tiny.en".to_owned(),\n',
    '            model_id: "tiny.en".to_owned(),\n            word_timestamps: false,\n')

# The toolbar exposes a native three-way mode, no BAT or external subtitle file.
replace(CAP,
    "    SizeChanged(i32),\n",
    "    SizeChanged(i32),\n    /// 0 phrases, 1 semantic punctuation, 2 timed words.\n    ModeChanged(i32),\n")
replace(CAP,
    "    look: (f64, f64),\n    /// The transcriber model,",
    "    look: (f64, f64),\n    mode: usize,\n    /// The transcriber model,")
replace(CAP,
    "    pub size: usize,\n    pub running: bool,",
    "    pub size: usize,\n    /// 0 original phrases, 1 break sentences, 2 karaoke words.\n    pub mode: usize,\n    pub running: bool,")
replace(CAP,
    "            CaptionsMsg::SizeChanged(index) => self.size = (index.max(0) as usize).min(2),\n",
    """            CaptionsMsg::SizeChanged(index) => self.size = (index.max(0) as usize).min(2),
            CaptionsMsg::ModeChanged(index) => self.mode = (index.max(0) as usize).min(2),
""")
replace(CAP,
    "                        let commands: Vec<Command> = segments\n                            .into_iter()\n",
    "                        let commands: Vec<Command> = arrange_segments(segments, subject.mode)\n                            .into_iter()\n")
replace(CAP,
    "            model_id: model.clone(),\n",
    "            model_id: model.clone(),\n            word_timestamps: self.mode == 2,\n")
replace(CAP,
    "            look: self.look(),\n            model,\n",
    "            look: self.look(),\n            mode: self.mode,\n            model,\n")
replace(CAP,
    "            size: self.size as i32,\n",
    "            size: self.size as i32,\n            mode: self.mode as i32,\n")
replace(CAP,
    "/// Imported cues keep the file's timing, including captions shorter than\n",
    """/// Convert one speech pass into editable title clips without a BAT. Modes:
/// original Whisper phrases, punctuation-aware speech or word karaoke.
/// Full diarization (actual speaker identity) is NOT inferred here.
fn arrange_segments(segments: Vec<Segment>, mode: usize) -> Vec<Segment> {
    let mut result = Vec::new();
    for segment in segments {
        if mode == 0 {
            result.push(segment);
            continue;
        }
        if mode == 2 {
            let mut words = segment.words.clone();
            // Fallback when Whisper's experimental timestamps are absent:
            // proportional word durations, explicitly approximate.
            if words.is_empty() {
                let parts: Vec<&str> = segment.text.split_whitespace().collect();
                let total = parts.iter().map(|w| w.chars().count()).sum::<usize>().max(1) as f64;
                let mut consumed = 0.0;
                for word in parts {
                    let portion = word.chars().count() as f64 / total;
                    let start = segment.start + (segment.end - segment.start) * consumed;
                    consumed += portion;
                    let end = segment.start + (segment.end - segment.start) * consumed;
                    words.push(concat_speech::transcribe::WordTiming {
                        start, end, text: word.to_owned(),
                    });
                }
            }
            for word in words {
                if word.end > word.start && !word.text.trim().is_empty() {
                    result.push(Segment {
                        start: word.start, end: word.end,
                        text: word.text, words: Vec::new(),
                    });
                }
            }
            continue;
        }
        // Keep terminal punctuation on its sentence; opening inverted
        // question/exclamation marks begin a fresh caption even without a
        // whitespace separator. Ignore ordinary commas.
        let text = segment.text.trim();
        let mut sentences: Vec<String> = Vec::new();
        let mut current = String::new();
        let chars: Vec<char> = text.chars().collect();
        for (index, ch) in chars.iter().enumerate() {
            if (*ch == '¿' || *ch == '¡') && !current.trim().is_empty() {
                sentences.push(current.trim().to_owned());
                current.clear();
            }
            current.push(*ch);
            if matches!(*ch, '.' | '?' | '!' | '。' | '！' | '？')
                && (index + 1 == chars.len()
                    || chars[index + 1].is_whitespace()
                    || chars[index + 1] == '¿'
                    || chars[index + 1] == '¡')
            {
                sentences.push(current.trim().to_owned());
                current.clear();
            }
        }
        if !current.trim().is_empty() { sentences.push(current.trim().to_owned()); }
        let total = sentences.iter().map(|s| s.chars().count()).sum::<usize>().max(1) as f64;
        let mut fraction = 0.0;
        for sentence in sentences {
            let first = segment.start + (segment.end - segment.start) * fraction;
            fraction += sentence.chars().count() as f64 / total;
            let last = segment.start + (segment.end - segment.start) * fraction;
            if last > first {
                result.push(Segment { start: first, end: last, text: sentence, words: Vec::new() });
            }
        }
    }
    result
}

/// Imported cues keep the file's timing, including captions shorter than""")
replace(CAP,
    "    use super::{script_captions, source_label};",
    "    use super::{arrange_segments, script_captions, source_label};")
replace(CAP,
    '    use super::{arrange_segments, script_captions, source_label};',
    """    use super::{arrange_segments, script_captions, source_label};
    use concat_speech::transcribe::Segment;

    #[test]
    fn one_whisper_phrase_splits_before_next_question() {
        let source = vec![Segment {
            start: 0.0, end: 4.0,
            text: "Iglesia para Dios. ¿Cuál es la pregunta?".to_owned(),
            words: vec![],
        }];
        let separated = arrange_segments(source, 1);
        assert_eq!(separated.len(), 2);
        assert_eq!(separated[0].text, "Iglesia para Dios.");
        assert_eq!(separated[1].text, "¿Cuál es la pregunta?");
        assert!((separated[1].end - 4.0).abs() < 1e-6);
    }

    #[test]
    fn karaoke_respects_per_word_timing() {
        let source = vec![Segment {
            start: 1.0, end: 3.0, text: "Hola mundo".to_owned(),
            words: vec![
                concat_speech::transcribe::WordTiming {
                    start: 1.1, end: 1.5, text: "Hola".to_owned(),
                },
                concat_speech::transcribe::WordTiming {
                    start: 2.0, end: 2.5, text: "mundo".to_owned(),
                },
            ],
        }];
        let separated = arrange_segments(source, 2);
        assert_eq!(separated.len(), 2);
        assert_eq!(separated[0].text, "Hola");
        assert_eq!(separated[1].start, 2.0);
    }
""")

replace(DIALOG,
    "    size: int,\n    running: bool,",
    "    size: int,\n    /// 0 standard, 1 punctuation, 2 word karaoke.\n    mode: int,\n    running: bool,")
replace(DIALOG,
    "    callback size-changed(index: int);\n",
    "    callback size-changed(index: int);\n    callback mode-changed(index: int);\n")
replace(DIALOG,
    '            DialogRow {\n                label: I18n.t("common.size");',
    """            if root.from-voice: DialogRow {
                label: "Estilo";
                SegmentedControl {
                    options: ["Normal", "Oraciones", "Karaoke"];
                    current: root.data.mode;
                    changed(index) => { root.mode-changed(index); }
                }
            }

            DialogRow {
                label: I18n.t("common.size");""")
replace(APP,
    "    callback captions-size-changed(index: int);\n",
    "    callback captions-size-changed(index: int);\n    callback captions-mode-changed(index: int);\n")
replace(APP,
    "            size-changed(index) => { root.captions-size-changed(index); }\n",
    "            size-changed(index) => { root.captions-size-changed(index); }\n            mode-changed(index) => { root.captions-mode-changed(index); }\n")
replace(LIB,
    "    app.on_captions_begin(on_window!(|state| {\n",
    """    app.on_captions_mode_changed(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::ModeChanged(index)));
    }));
    app.on_captions_begin(on_window!(|state| {
""")
print("Estudio Joven: karaoke y separación contextual integrados.")
