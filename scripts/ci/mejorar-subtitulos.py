#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Caption-only improvements on the known-good Windows CPU build.

Runs after text-motion.patch and integrar-subtitulos.py. Fails loudly when
Concat changes, rather than silently shipping non-working controls.
"""
from pathlib import Path
import shutil


def replace(path: str, before: str, after: str) -> None:
    file = Path(path)
    content = file.read_text(encoding="utf-8")
    if content.count(before) != 1:
        raise RuntimeError(f"Missing/ambiguous anchor in {path}: {before[:110]!r} ({content.count(before)})")
    file.write_text(content.replace(before, after, 1), encoding="utf-8")


SPEECH = "src/crates/concat-speech/src/transcribe.rs"
CAP = "src/crates/concat/src/panes/captions.rs"
DIALOG = "src/crates/concat/ui/dialogs/captions.slint"
APP = "src/crates/concat/ui/app.slint"
LIB = "src/crates/concat/src/lib.rs"

source = Path(".estudio-joven/scripts/ci/caption_words.rs")
target = Path("src/crates/concat-project/src/caption_words.rs")
if not source.is_file():
    raise RuntimeError(f"Missing caption segmentation module: {source}")
shutil.copyfile(source, target)
with Path("src/crates/concat-project/src/lib.rs").open("a", encoding="utf-8") as out:
    out.write("\n/// Reusable word-level and short-phrase caption segmentation.\npub mod caption_words;\n")

# Word timestamps are requested for both phrase grouping and karaoke pop.
replace(CAP,
    "            word_timestamps: self.mode == 2,",
    "            word_timestamps: self.mode != 0,")
# Reset dialog must preserve the previously chosen mode and appearance.
replace(CAP,
    """        *self = CaptionsPane {
            open: true,
            from_voice,
            clip,
            chosen_with: studio.sole_selection(),
            model,
            placement: 0,
            size: 1,""",
    """        let (mode, length, colour, font, effect, animation_speed) =
            (self.mode, self.length, self.colour, self.font, self.effect, self.animation_speed);
        *self = CaptionsPane {
            open: true,
            from_voice,
            clip,
            chosen_with: studio.sole_selection(),
            model,
            mode, length, colour, font, effect, animation_speed,
            placement: 0,
            size: 1,""")
# Additional selectors are genuine model state, not UI-only switches.
replace(CAP,
    "    ModeChanged(i32),\n",
    """    ModeChanged(i32),
    LengthChanged(i32),
    ColourChanged(i32),
    FontChanged(i32),
    EffectChanged(i32),
    AnimationSpeedChanged(i32),
""")
replace(CAP,
    "    pub mode: usize,\n    pub running: bool,",
    """    pub mode: usize,
    /// 0 short (24 chars), 1 medium (42), 2 long (60).
    pub length: usize,
    /// 0 project style, 1 white, 2 yellow, 3 cyan, 4 coral, 5 mint.
    pub colour: usize,
    /// 0 saved/imported style, 1 Hanken Grotesk, 2 Cabinet Grotesk.
    pub font: usize,
    /// 0 none, 1 fade, 2 slide, 3 zoom, 4 gentle bounce.
    pub effect: usize,
    /// 0 fast, 1 balanced, 2 slow.
    pub animation_speed: usize,
    pub running: bool,""")
# Default values without writing a custom impl Default for the whole pane.
replace(CAP,
    "        let (mode, length, colour, font, effect, animation_speed) =",
    """        // On a first opening, start with a gentle pop preset for karaoke;
        // the effect is only applied when Karaoke is selected.
        let (mode, length, colour, font, effect, animation_speed) =""")
replace(CAP,
    "            CaptionsMsg::ModeChanged(index) => self.mode = (index.max(0) as usize).min(2),\n",
    """            CaptionsMsg::ModeChanged(index) => self.mode = (index.max(0) as usize).min(2),
            CaptionsMsg::LengthChanged(index) => self.length = (index.max(0) as usize).min(2),
            CaptionsMsg::ColourChanged(index) => self.colour = (index.max(0) as usize).min(5),
            CaptionsMsg::FontChanged(index) => self.font = (index.max(0) as usize).min(2),
            CaptionsMsg::EffectChanged(index) => self.effect = (index.max(0) as usize).min(4),
            CaptionsMsg::AnimationSpeedChanged(index) =>
                self.animation_speed = (index.max(0) as usize).min(2),
""")
# Start with soft pop by default when user activates karaoke the first time.
# A mode change preserves the user's manual choices once set.
replace(CAP,
    "            CaptionsMsg::ModeChanged(index) => self.mode = (index.max(0) as usize).min(2),",
    """            CaptionsMsg::ModeChanged(index) => {
                self.mode = (index.max(0) as usize).min(2);
                if self.mode == 2 && self.effect == 0 {
                    self.effect = 4; // gentle bounce
                }
            },""")
replace(CAP,
    "    mode: usize,\n    /// The transcriber model,",
    """    mode: usize,
    length: usize,
    style: Option<TextStyle>,
    /// The transcriber model,""")
replace(CAP,
    "                        let base = studio.prefs.title_style.clone();\n                        let commands: Vec<Command> = arrange_segments(segments, subject.mode)",
    """                        // Keep the settings the user selected when the job began.
                        let base = subject.style;
                        let commands: Vec<Command> = arrange_segments(segments, subject.mode, subject.length)""")
# The 0.2-second minimum kept ultra-short captions overlapping, and the
# editor's AddTextClip enforces its own 1/60-second minimum.
replace(CAP,
    "                                        ((segment.end - segment.start) / subject.speed).max(0.2),",
    "                                        ((segment.end - segment.start) / subject.speed).max(1.0 / 60.0),")
replace(CAP,
    "            look: self.look(),\n            mode: self.mode,\n            model,",
    """            look: self.look(),
            mode: self.mode,
            length: self.length,
            style: self.caption_style(studio.prefs.title_style.as_ref()),
            model,""")
replace(CAP,
    "        let base = studio.prefs.title_style.clone();\n        let commands: Vec<Command> = lines\n",
    "        let base = self.caption_style(studio.prefs.title_style.as_ref());\n        let commands: Vec<Command> = lines\n")
# In script mode reuse robust phrase/word splitting before rendering commands.
replace(CAP,
    """        let commands: Vec<Command> = lines
            .into_iter()
            .map(|(text, seconds)| {
                let command = caption_clip(text, at, seconds, look, base.as_ref());
                at += seconds;
                command
            })
            .collect();""",
    """        let segments: Vec<Segment> = lines.into_iter().map(|(text, seconds)| {
            let start = at;
            at += seconds;
            Segment { start, end: at, text, words: Vec::new() }
        }).collect();
        let commands: Vec<Command> = arrange_segments(segments, self.mode, self.length)
            .into_iter()
            .map(|part| caption_clip(
                part.text, part.start, (part.end - part.start).max(1.0 / 60.0),
                look, base.as_ref()
            ))
            .collect();""")
replace(CAP,
    "    /// A caption's look, by the sheet's rows: where it sits and its size.\n    fn look(&self) -> (f64, f64) {",
    """    /// Preserve the imported font or saved title's own appearance unless
    /// the user explicitly selects one of the caption presets. These styles
    /// become ordinary editable text properties after generating captions.
    fn caption_style(&self, saved: Option<&TextStyle>) -> Option<TextStyle> {
        let mut style = saved.cloned().unwrap_or_default();
        style.color = match self.colour {
            1 => "#FFFFFF".to_owned(),
            2 => "#FFE450".to_owned(),
            3 => "#48DDFC".to_owned(),
            4 => "#FF7D8B".to_owned(),
            5 => "#7BF2AF".to_owned(),
            _ => style.color,
        };
        style.font_family = match self.font {
            1 => "Hanken Grotesk".to_owned(),
            2 => "\\"Cabinet Grotesk\\"".to_owned(),
            _ => style.font_family,
        };
        if self.mode == 2 {
            if style.stroke_width == 0.0 {
                style.stroke_width = 0.0018;
                style.stroke_color = "#121212".to_owned();
            }
            style.font_weight = style.font_weight.max(650.0);
            style.motion = concat_project::text_motion::TextMotion {
                entrance: self.effect as u8,
                exit: 0,
                in_seconds: [0.12, 0.18, 0.26][self.animation_speed.min(2)],
                out_seconds: 0.1,
                intensity: if self.effect == 4 { 0.62 } else { 0.75 },
            };
        }
        Some(style)
    }

    /// A caption's look, by the sheet's rows: where it sits and its size.
    fn look(&self) -> (f64, f64) {""")
replace(CAP,
    "            mode: self.mode as i32,\n",
    """            mode: self.mode as i32,
            length: self.length as i32,
            colour: self.colour as i32,
            font: self.font as i32,
            effect: self.effect as i32,
            animation_speed: self.animation_speed as i32,
""")
# Word-aware grouping, never use raw Whisper subword segmentation as UI clips.
start = Path(CAP).read_text(encoding="utf-8")
first = start.index("fn arrange_segments(segments: Vec<Segment>, mode: usize) -> Vec<Segment> {")
last = start.index("/// Imported cues keep the file's timing", first)
new = """fn arrange_segments(segments: Vec<Segment>, mode: usize, length: usize) -> Vec<Segment> {
    let mut output = Vec::new();
    for segment in segments {
        if mode == 0 {
            output.push(segment);
            continue;
        }
        let timing: Vec<concat_project::caption_words::Word> = segment.words.iter().map(|word|
            concat_project::caption_words::Word {
                text: word.text.clone(), start: word.start, end: word.end,
            }
        ).collect();
        let words = if mode == 2 {
            concat_project::caption_words::split(
                &segment.text, segment.start, segment.end, timing
            )
        } else {
            let (chars, words) = [(24, 5), (42, 8), (60, 11)][length.min(2)];
            concat_project::caption_words::phrases(
                &segment.text, segment.start, segment.end, timing, chars, words
            )
        };
        output.extend(words.into_iter().filter_map(|word| {
            (word.end > word.start && !word.text.trim().is_empty()).then_some(Segment {
                start: word.start,
                end: word.end,
                text: word.text,
                words: Vec::new(),
            })
        }));
    }
    output
}

"""
Path(CAP).write_text(start[:first] + new + start[last:], encoding="utf-8")
# The original tests now call arrange_segments(...,mode,length).
replace(CAP, "arrange_segments(source, 1);", "arrange_segments(source, 1, 2);")
replace(CAP, "arrange_segments(source, 2);", "arrange_segments(source, 2, 1);")

replace(DIALOG,
    "    mode: int,\n    running: bool,",
    """    mode: int,
    length: int,
    colour: int,
    font: int,
    effect: int,
    animation-speed: int,
    running: bool,""")
replace(DIALOG,
    "    callback mode-changed(index: int);\n",
    """    callback mode-changed(index: int);
    callback length-changed(index: int);
    callback colour-changed(index: int);
    callback font-changed(index: int);
    callback effect-changed(index: int);
    callback animation-speed-changed(index: int);
""")
replace(DIALOG,
    """            if root.from-voice: DialogRow {
                label: "Estilo";
                SegmentedControl {
                    options: ["Normal", "Oraciones", "Karaoke"];
                    current: root.data.mode;
                    changed(index) => { root.mode-changed(index); }
                }
            }""",
    """            DialogRow {
                label: "Modo";
                SegmentedControl {
                    options: ["Normal", "Frases", "Karaoke pop"];
                    current: root.data.mode;
                    changed(index) => { root.mode-changed(index); }
                }
            }

            if root.data.mode == 1: DialogRow {
                label: "Texto por bloque";
                SegmentedControl {
                    options: ["Corto", "Medio", "Largo"];
                    current: root.data.length;
                    changed(index) => { root.length-changed(index); }
                }
            }

            DialogRow {
                label: "Color";
                Select {
                    options: ["Estilo guardado", "Blanco", "Amarillo", "Cian", "Coral", "Menta"];
                    current: root.data.colour;
                    changed(index) => { root.colour-changed(index); }
                }
            }

            DialogRow {
                label: "Fuente";
                Select {
                    options: ["Estilo guardado", "Hanken Grotesk", "Cabinet Grotesk"];
                    current: root.data.font;
                    changed(index) => { root.font-changed(index); }
                }
            }

            if root.data.mode == 2: DialogRow {
                label: "Animacion";
                Select {
                    options: ["Ninguna", "Desvanecer", "Deslizar", "Zoom", "Rebote suave"];
                    current: root.data.effect;
                    changed(index) => { root.effect-changed(index); }
                }
            }

            if root.data.mode == 2 && root.data.effect != 0: DialogRow {
                label: "Velocidad";
                SegmentedControl {
                    options: ["Rapida", "Suave", "Lenta"];
                    current: root.data.animation-speed;
                    changed(index) => { root.animation-speed-changed(index); }
                }
            }

            if root.data.mode == 2: Text {
                text: "Una palabra por clip, editable en Texto. Para cambiar a una fuente importada, usa Texto > Usar para nuevos titulos y elige Estilo guardado. Los tiempos sin alineacion exacta son aproximados.";
                wrap: word-wrap;
                color: Theme.fg-muted;
                font-size: Theme.fs-sm;
            }""")
replace(APP,
    "    callback captions-mode-changed(index: int);\n",
    """    callback captions-mode-changed(index: int);
    callback captions-length-changed(index: int);
    callback captions-colour-changed(index: int);
    callback captions-font-changed(index: int);
    callback captions-effect-changed(index: int);
    callback captions-animation-speed-changed(index: int);
""")
replace(APP,
    "            mode-changed(index) => { root.captions-mode-changed(index); }\n",
    """            mode-changed(index) => { root.captions-mode-changed(index); }
            length-changed(index) => { root.captions-length-changed(index); }
            colour-changed(index) => { root.captions-colour-changed(index); }
            font-changed(index) => { root.captions-font-changed(index); }
            effect-changed(index) => { root.captions-effect-changed(index); }
            animation-speed-changed(index) => { root.captions-animation-speed-changed(index); }
""")
replace(LIB,
    "    app.on_captions_begin(on_window!(|state| {\n",
    """    app.on_captions_length_changed(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::LengthChanged(index)));
    }));
    app.on_captions_colour_changed(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::ColourChanged(index)));
    }));
    app.on_captions_font_changed(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::FontChanged(index)));
    }));
    app.on_captions_effect_changed(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::EffectChanged(index)));
    }));
    app.on_captions_animation_speed_changed(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::AnimationSpeedChanged(index)));
    }));
    app.on_captions_begin(on_window!(|state| {
""")
# Short word clips have 3-12 frames at 30fps. Generating hundreds of
# keyframes per word wastes RAM/CPU without making the animation smoother.
MOTION = "src/crates/concat-project/src/text_motion.rs"
replace(MOTION,
    """        for i in 0..=90 {
            let t = f64::from(i) / 90.0;""",
    """        let samples = ((duration * 60.0).ceil() as usize).clamp(4, 24);
        for i in 0..=samples {
            let t = i as f64 / samples as f64;""")
print("Estudio Joven: phrase segmentation, editable word karaoke, styles, smooth pop applied without CUDA.")
