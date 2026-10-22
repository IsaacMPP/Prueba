#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate speech recognition, transcript correction and caption generation.

Keeps word timing in one UI session and never retranscribes just because
the user changes subtitle length/style. A different source invalidates it.
"""
from pathlib import Path

def replace(path, before, after):
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError(f"{path}: missing/nonunique anchor ({text.count(before)}): {before[:140]!r}")
    file.write_text(text.replace(before, after, 1), encoding="utf-8")

CAP="src/crates/concat/src/panes/captions.rs"
DIALOG="src/crates/concat/ui/dialogs/captions.slint"
APP="src/crates/concat/ui/app.slint"
LIB="src/crates/concat/src/lib.rs"

replace(CAP,
    "    TextEdited(String),\n",
    "    TextEdited(String),\n    /// Explicit fresh speech-to-text run; discards cached draft for this clip.\n    Transcribe,\n")
replace(CAP,
    "struct Subject {\n",
    "struct Subject {\n    /// Source identity: never reuse transcript on another media clip.\n    clip_id: String,\n")
replace(CAP,
    "/// Seconds whisper takes over one thirty-second window,",
    """#[derive(Clone, Debug)]
struct CachedVoice {
    subject: Subject,
    segments: Vec<Segment>,
    original_text: String,
}

/// Seconds whisper takes over one thirty-second window,""")
replace(CAP,
    "    /// The script's words.\n    pub text: String,",
    """    /// Editable original transcript (or a typed script), not subtitle clips.
    pub text: String,
    cached_voice: Option<CachedVoice>,""")
replace(CAP,
    "            CaptionsMsg::TextEdited(text) => self.text = text,\n",
    "            CaptionsMsg::TextEdited(text) => self.text = text,\n            CaptionsMsg::Transcribe => self.run_sound(studio),\n")
replace(CAP,
    "                    self.chosen_with = studio.sole_selection();\n                    self.message.clear();\n                }\n            }\n            CaptionsMsg::TextEdited",
    """                    self.chosen_with = studio.sole_selection();
                    self.message.clear();
                    self.cached_voice = None;
                    self.text.clear();
                }
            }
            CaptionsMsg::TextEdited""")
replace(CAP,
    """            CaptionsMsg::Begin => {
                if self.from_voice {
                    self.run_sound(studio);
                } else {
                    self.run_script(studio);
                }
            }""",
    """            CaptionsMsg::Begin => {
                if self.from_voice {
                    if self.cached_voice.is_some() {
                        self.generate_from_transcript(studio);
                    } else {
                        self.run_sound(studio);
                    }
                } else {
                    self.run_script(studio);
                }
            }""")
# Replace the current automatic "Finished => create clips" branch with an
# editable, reusable transcript stored in pane session memory.
source=Path(CAP).read_text(encoding="utf-8")
start=source.index("                    Ok(segments) => {",source.index("            CaptionsMsg::Finished(result)"))
end=source.index("                    // Asked for: the sheet",start)
new="""                    Ok(segments) => {
                        let Some(subject) = subject else { return; };
                        if segments.is_empty() {
                            self.message = t("captions.nothingSaidClip");
                            return;
                        }
                        let original_text = segments.iter()
                            .map(|s| s.text.trim())
                            .filter(|s| !s.is_empty())
                            .collect::<Vec<_>>().join(" ");
                        self.text = original_text.clone();
                        self.cached_voice = Some(CachedVoice {
                            subject,
                            segments,
                            original_text,
                        });
                        self.message = "Transcripción lista. Corrige las palabras y pulsa Generar subtítulos. Cambiar la longitud o el estilo no vuelve a ejecutar Whisper.".to_owned();
                    }
"""
Path(CAP).write_text(source[:start]+new+source[end:],encoding="utf-8")
# Preserve cached transcript when the sheet is reopened on its original clip.
replace(CAP,
    """        let (mode, length, colour, font, effect, animation_speed) =
            (self.mode, self.length, self.colour, self.font, self.effect, self.animation_speed);""",
    """        let (mode, length, colour, font, effect, animation_speed) =
            (self.mode, self.length, self.colour, self.font, self.effect, self.animation_speed);
        let kept = self.cached_voice.take().filter(|c|
            Some(c.subject.clip_id.as_str()) == clip.as_deref());
        let text = if kept.is_some() { self.text.clone() } else { String::new() };""")
replace(CAP,
    "            mode, length, colour, font, effect, animation_speed, effect_customized,\n",
    "            mode, length, colour, font, effect, animation_speed, effect_customized,\n            cached_voice: kept,\n            text,\n")
replace(CAP,
    "            word_timestamps: self.mode != 0,",
    "            // Always retain timing, even when 'Normal' was selected.\n            word_timestamps: true,")
replace(CAP,
    "        self.subject = Some(Subject {\n            start: clip.start,",
    "        self.subject = Some(Subject {\n            clip_id: clip.id.clone(),\n            start: clip.start,")
# Add an actual action for the second stage. Existing caption clip creation
# is reused, retaining the same style and one-clip-per-phrase engine.
replace(CAP,
    "    /// The script as titles, one after another from the playhead.\n",
    """    /// Create subtitles from cached word clocks, without Whisper.
    fn generate_from_transcript(&mut self, studio: &mut Studio) {
        let Some(cached) = self.cached_voice.clone() else {
            self.message = "Primero transcribe el audio.".to_owned();
            return;
        };
        if cached.segments.is_empty() || self.text.trim().is_empty() {
            self.message = "La transcripción está vacía.".to_owned();
            return;
        }
        let subject = cached.subject;
        // When only spelling/words change, retain the original alignment
        // as long as word count agrees. Added/deleted words invalidate
        // timing; use proportional seconds until user re-aligns the draft.
        let original: Vec<concat_project::caption_words::Word> = cached.segments.iter()
            .flat_map(|seg| concat_project::caption_words::split(
                &seg.text, seg.start, seg.end,
                seg.words.iter().map(|w| concat_project::caption_words::Word {
                    text: w.text.clone(), start: w.start, end: w.end,
                }).collect()
            )).collect();
        let typed: Vec<&str> = self.text.split_whitespace().collect();
        let segments: Vec<Segment> = if self.text.trim() == cached.original_text.trim() {
            cached.segments
        } else {
            let start = original.first().map_or(0.0, |w| w.start);
            let end = original.last().map_or(0.0, |w| w.end);
            if end <= start { self.message = "No hay tiempos válidos.".into(); return; }
            let words = if original.len() == typed.len() {
                typed.iter().zip(&original).map(|(text, old)|
                    concat_speech::transcribe::WordTiming {
                        text: (*text).to_owned(), start: old.start, end: old.end
                    }).collect()
            } else {
                self.message = "Cambió la cantidad de palabras; los tiempos generados son aproximados. Vuelve a transcribir o corrige la sincronización cuando sea necesario.".into();
                Vec::new()
            };
            vec![Segment { text: self.text.clone(), start, end, words }]
        };
        let count_mode = self.mode;
        let length = self.length;
        let base = self.caption_style(studio.prefs.title_style.as_ref());
        let look = self.look();
        let commands: Vec<Command> = arrange_segments(segments, count_mode, length)
            .into_iter()
            .filter(|s| !s.text.trim().is_empty() && s.end > s.start)
            .map(|segment| {
                let mut style = base.clone().unwrap_or_default();
                if count_mode == 2 {
                    style.karaoke = Some(concat_project::model::KaraokeTrack {
                        active_color: "#FFE040".into(),
                        words: segment.words.iter().take(12).map(|w|
                            concat_project::model::KaraokeWord {
                                start: (w.start - segment.start) / subject.speed,
                                end: (w.end - segment.start) / subject.speed,
                            }).collect(),
                    });
                } else { style.karaoke = None; }
                caption_clip(
                    segment.text,
                    subject.start + segment.start / subject.speed,
                    ((segment.end - segment.start) / subject.speed).max(1.0 / 60.0),
                    look, Some(&style),
                )
            }).collect();
        if commands.is_empty() {
            self.message = t("captions.nothingSaidClip");
            return;
        }
        let count = commands.len();
        studio.apply(Command::Batch { commands });
        studio.notify(&tf("captions.addedCaptions", &[&count]), false);
        self.open = false;
    }

    /// The script as titles, one after another from the playhead.
""")
# expose two steps to Slint
replace(CAP,
    "            mode: self.mode as i32,\n",
    "            mode: self.mode as i32,\n            has_transcript: self.cached_voice.is_some(),\n")
replace(DIALOG,
    "    mode: int,\n",
    "    mode: int,\n    has-transcript: bool,\n")
replace(DIALOG,
    "    callback begin();\n",
    "    callback begin();\n    callback transcribe();\n")
replace(APP,
    "    callback captions-begin();\n",
    "    callback captions-begin();\n    callback captions-transcribe();\n")
replace(APP,
    "            begin => { root.captions-begin(); }\n",
    "            begin => { root.captions-begin(); }\n            transcribe => { root.captions-transcribe(); }\n")
replace(LIB,
    "    app.on_captions_begin(on_window!(|state| {\n",
    """    app.on_captions_transcribe(on_window!(|state| {
        state.handle(Msg::Captions(CaptionsMsg::Transcribe));
    }));
    app.on_captions_begin(on_window!(|state| {
""")
replace(DIALOG,
    "        if !root.data.running && !root.from-voice: DialogSection {",
    "        if !root.data.running && (!root.from-voice || root.data.has-transcript): DialogSection {")
replace(DIALOG,
    '            title: I18n.t("common.script");',
    '            title: root.from-voice ? "Transcripción editable" : I18n.t("common.script");')
replace(DIALOG,
    '                label: root.from-voice ? I18n.t("captions.generateCaptions") : I18n.t("captions.addCaptions");',
    '                label: root.from-voice ? (root.data.has-transcript ? "2. Generar subtítulos" : "1. Transcribir voz") : I18n.t("captions.addCaptions");')
replace(DIALOG,
    """            // Captions as a SubRip file: one read in as titles with the
""",
    """            if !root.data.running && root.from-voice && root.data.has-transcript: Button {
                block: true;
                ghost: true;
                label: "Volver a transcribir";
                clicked => { root.transcribe(); }
            }

            // Captions as a SubRip file: one read in as titles with the
""")
print("Transcript-first workflow: recognition -> edit -> generate; no CUDA.")
