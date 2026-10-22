#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""One timeline clip per Karaoke phrase, one GPU colour pass per clip.

Run after Estudio Joven's existing CPU-only subtitle patches. Keep the full
sentence rasterized once and re-colour only the active word using Concat's
already cached per-word RevealMap. No CUDA, per-word title tracks or PNGs.
"""
from pathlib import Path


def replace(path: str, before: str, after: str):
    f = Path(path)
    source = f.read_text(encoding="utf-8")
    if source.count(before) != 1:
        raise RuntimeError(f"{path}: expected exactly one anchor ({source.count(before)}): {before[:120]!r}")
    f.write_text(source.replace(before, after, 1), encoding="utf-8")


MODEL = "src/crates/concat-project/src/model.rs"
CAP = "src/crates/concat/src/panes/captions.rs"
TITLES = "src/crates/concat-host/src/titles.rs"
STUDIO = "src/crates/concat/src/studio.rs"
PANEL = "src/crates/concat/ui/inspector/text-panel.slint"
UI = "src/crates/concat/ui/timeline/model.slint"

replace(MODEL,
    "pub struct TextStyle {\n",
    """pub struct TextStyle {
    /// Word-aligned caption metadata. Optional, so old projects still load.
    pub karaoke: Option<KaraokeTrack>,
""")
replace(MODEL,
    "impl TextStyle {\n",
    """/// One local word clock, in seconds since the title clip begins.
#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, PartialEq, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KaraokeWord {
    pub start: f64,
    pub end: f64,
}

/// One phrase remains in one title: its colour can be edited like the
/// existing title colour and its word times are evaluated by a shader.
#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, PartialEq, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct KaraokeTrack {
    pub active_color: String,
    pub words: Vec<KaraokeWord>,
}

impl TextStyle {
""")
replace(MODEL,
    "        self.motion = self.motion.tidy();",
    """        self.motion = self.motion.tidy();
        // Malformed or huge metadata from hand-edited files must never
        // crash or stall the renderer. Phrases use at most 12 words.
        if let Some(karaoke) = &mut self.karaoke {
            karaoke.words.retain(|w|
                w.start.is_finite() && w.end.is_finite()
                && w.start >= 0.0 && w.end > w.start);
            if karaoke.words.is_empty() || karaoke.words.len() > 12 {
                self.karaoke = None;
            }
        }""")
replace(MODEL,
    "            motion: crate::text_motion::TextMotion::default(),",
    """            motion: crate::text_motion::TextMotion::default(),
            karaoke: None,""")

# Format 2 WGSL filter: Concat already binds the title's RevealMap in group 3,
# and frame.clip_time gives the current time relative to the title.
directory = Path("src/crates/concat-effects/packages/concat.karaoke")
directory.mkdir(parents=True, exist_ok=True)
parameters = [
    ("word_count", "Words", 1, 12, 1),
    ("red", "Active Red", 0, 255, 255),
    ("green", "Active Green", 0, 255, 222),
    ("blue", "Active Blue", 0, 255, 64),
]
for index in range(12):
    parameters.extend([
        (f"s{index}", f"Word {index + 1} Start", 0, 36000, 0),
        (f"e{index}", f"Word {index + 1} End", 0, 36000, 0),
    ])
manifest = """format = 2
[effect]
id = "concat.karaoke"
name = "Karaoke palabra activa"
version = 1
kind = "effect"
category = "Text"
order = 60
description = "Resalta la palabra que se está pronunciando sin dividir la frase en clips."
"""
for key, label, minv, maxv, default in parameters:
    manifest += f'\n[[param]]\nkey = "{key}"\nlabel = "{label}"\nmin = {minv}\nmax = {maxv}\ndefault = {default}\nstep = 0.01\n'
manifest += '\n[wgsl]\nentry = "effect.wgsl"\n'
(directory / "effect.toml").write_text(manifest, encoding="utf-8")
shader = "struct Params {\n" + "\n".join(f"    {key}: f32," for key, *_ in parameters) + "\n}\n"
shader += """
fn effect(uv: vec2<f32>) -> vec4<f32> {
    let c = sample(uv);
    if (c.a <= 0.001 || params.word_count < 1.0) {
        return c;
    }
    let ordinal = round(reveal_order(uv) * max(params.word_count - 1.0, 1.0));
    var begin = -1.0;
    var finish = -1.0;
"""
for i in range(12):
    shader += f"    if (ordinal == {i}.0 && params.word_count > {i}.0) {{ begin = params.s{i}; finish = params.e{i}; }}\n"
shader += """
    // A brief smooth dissolve; no blinking or hard one-frame cuts.
    if (finish <= begin) { return c; }
    let enter = smoothstep(begin - 0.025, begin + 0.035, frame.clip_time);
    let leave = 1.0 - smoothstep(finish - 0.015, finish + 0.055, frame.clip_time);
    let strength = clamp(enter * leave, 0.0, 1.0);
    let chosen = from_display(vec3<f32>(params.red, params.green, params.blue) / 255.0);
    return vec4<f32>(mix(c.rgb, chosen, strength), c.a);
}
"""
(directory / "effect.wgsl").write_text(shader, encoding="utf-8")

# Paint once; derive one constant filter from the style metadata, not a
# command per word. The clip carries the filter as part of the same
# ExportClip for both monitor and file exporter.
replace(TITLES,
    "    ClipKind as ModelClipKind, Project, ShapeKind, ShapeStyle, TextAlign, TextStyle,",
    "    AppliedFilter, ClipKind as ModelClipKind, Project, ShapeKind, ShapeStyle, TextAlign, TextStyle,")
replace(TITLES,
    "                    effects: clip.video_effects.clone(),",
    """                    effects: {
                        let mut effects = clip.video_effects.clone();
                        if let Painting::Title(style) = painting {
                            if let Some(filter) = karaoke_filter(style) {
                                effects.push(filter);
                            }
                        }
                        effects
                    },""")
replace(TITLES,
    "/// The document's style, field for field, in the painter's terms.\n",
    """/// A single title plus a single shader-pass holds every word's clock.
fn karaoke_filter(style: &TextStyle) -> Option<AppliedFilter> {
    let track = style.karaoke.as_ref()?;
    if track.words.is_empty() || track.words.len() > 12 { return None; }
    let mut effect = AppliedFilter::new("concat.karaoke");
    effect.params.insert("word_count".to_owned(), track.words.len() as f64);
    for (i, word) in track.words.iter().enumerate() {
        effect.params.insert(format!("s{i}"), word.start);
        effect.params.insert(format!("e{i}"), word.end);
    }
    let hex = track.active_color.trim_start_matches('#');
    if hex.len() == 6 {
        if let Ok(rgb) = u32::from_str_radix(hex, 16) {
            effect.params.insert("red".to_owned(), ((rgb >> 16) & 255) as f64);
            effect.params.insert("green".to_owned(), ((rgb >> 8) & 255) as f64);
            effect.params.insert("blue".to_owned(), (rgb & 255) as f64);
        }
    }
    Some(effect)
}

/// The document's style, field for field, in the painter's terms.
""")

# Re-group Karaoke segments: groups of up to 8 words for a stable phrase.
# Their individual clocks remain stored in Segment.words, not separate clips.
src = Path(CAP).read_text(encoding="utf-8")
old = """        let words = if mode == 2 {
            concat_project::caption_words::split(
                &segment.text, segment.start, segment.end, timing
            )
        } else {"""
if src.count(old) != 1: raise RuntimeError("Karaoke group mode anchor missing")
new = """        let words = if mode == 2 {
            concat_project::caption_words::phrases(
                &segment.text, segment.start, segment.end, timing, 52, 8
            )
        } else {"""
src = src.replace(old,new)
# Fill word clocks for karaoke groups; use original (or safely estimated)
# word alignment so highlight is independent of block duration.
old = """        output.extend(words.into_iter().filter_map(|word| {
            (word.end > word.start && !word.text.trim().is_empty()).then_some(Segment {
                start: word.start,
                end: word.end,
                text: word.text,
                words: Vec::new(),
            })
        }));"""
if src.count(old)!=1: raise RuntimeError("Extend words anchor missing")
new = """        let lexical = if mode == 2 {
            concat_project::caption_words::split(&segment.text, segment.start, segment.end,
                segment.words.iter().map(|w| concat_project::caption_words::Word {
                    text: w.text.clone(), start: w.start, end: w.end,
                }).collect())
        } else { Vec::new() };
        output.extend(words.into_iter().filter_map(|word| {
            if word.end <= word.start || word.text.trim().is_empty() { return None; }
            let timed = if mode == 2 {
                lexical.iter().filter(|w| w.start >= word.start - 1e-6
                    && w.end <= word.end + 1e-6).map(|w|
                    concat_speech::transcribe::WordTiming {
                        start: w.start, end: w.end, text: w.text.clone(),
                    }).collect()
            } else { Vec::new() };
            Some(Segment { start: word.start, end: word.end, text: word.text, words: timed })
        }));"""
src=src.replace(old,new)
Path(CAP).write_text(src,encoding="utf-8")

# Mark karaoke clips at command generation time. The chosen active colour
# is editable later in the same inspector as the normal title fill.
replace(CAP,
    """                        let commands: Vec<Command> = arrange_segments(segments, subject.mode, subject.length)
                            .into_iter()
                            .filter_map(|segment| {""",
    """                        let commands: Vec<Command> = arrange_segments(segments, subject.mode, subject.length)
                            .into_iter()
                            .filter_map(|segment| {""") # verified anchor, see second insertion
replace(CAP,
    """                                    caption_clip(
                                        text,
                                        subject.start + segment.start / subject.speed,
                                        ((segment.end - segment.start) / subject.speed).max(1.0 / 60.0),
                                        look,
                                        base.as_ref(),
                                    )""",
    """                                    let mut style = base.clone().unwrap_or_default();
                                    if subject.mode == 2 {
                                        style.karaoke = Some(concat_project::model::KaraokeTrack {
                                            active_color: "#FFE040".to_owned(),
                                            words: segment.words.iter().take(12).map(|w|
                                                concat_project::model::KaraokeWord {
                                                    start: (w.start - segment.start) / subject.speed,
                                                    end: (w.end - segment.start) / subject.speed,
                                                }).collect(),
                                        });
                                    } else {
                                        style.karaoke = None;
                                    }
                                    caption_clip(
                                        text,
                                        subject.start + segment.start / subject.speed,
                                        ((segment.end - segment.start) / subject.speed).max(1.0 / 60.0),
                                        look,
                                        Some(&style),
                                    )""")
# Add karaoke clocks for captions created from typed scripts, no speech.
replace(CAP,
    """            .map(|part| caption_clip(
                part.text, part.start, (part.end - part.start).max(1.0 / 60.0),
                look, base.as_ref()
            ))""",
    """            .map(|part| {
                let mut style = base.clone().unwrap_or_default();
                style.karaoke = if self.mode == 2 {
                    Some(concat_project::model::KaraokeTrack {
                        active_color: "#FFE040".to_owned(),
                        words: part.words.iter().take(12).map(|w|
                            concat_project::model::KaraokeWord {
                                start: w.start - part.start,
                                end: w.end - part.start,
                            }).collect(),
                    })
                } else { None };
                caption_clip(part.text, part.start, (part.end - part.start).max(1.0 / 60.0),
                    look, Some(&style))
            })""")

# Any title retains its existing font/color/size editor; expose one more
# full-spectrum colour picker only when a karaoke phrase is selected.
replace(UI,
    "export enum ClipTextField {\n    content, font-family, color, stroke-color, background,",
    "export enum ClipTextField {\n    content, font-family, color, stroke-color, background, karaoke-color,")
replace(UI,
    "    fill-hex: string,\n",
    "    fill-hex: string,\n    karaoke: bool,\n    karaoke-color: color,\n")
replace(STUDIO,
    "            fill_hex: hex_of(fill).into(),",
    """            fill_hex: hex_of(fill).into(),
            karaoke: text.karaoke.is_some(),
            karaoke_color: text.karaoke.as_ref()
                .map_or(slint::Color::from_rgb_u8(255, 224, 64),
                    |track| colour_of(&track.active_color)),""")
replace(STUDIO,
    "                ClipTextField::Background => text.background = hex_with_alpha(value),",
    """                ClipTextField::Background => text.background = hex_with_alpha(value),
                ClipTextField::KaraokeColor => {
                    if let Some(track) = text.karaoke.as_mut() {
                        track.active_color = hex_of(value);
                    }
                },""")
replace(STUDIO,
    "        style.content.clear();\n        self.prefs.title_style = Some(style);",
    "        style.content.clear();\n        style.karaoke = None;\n        self.prefs.title_style = Some(style);")
replace(PANEL,
    """        ColourField {
            label: I18n.t("common.color");
            value: root.selected.fill;
            alpha: false;
            changed(colour) => { root.set-colour(ClipTextField.color, colour); root.commit(); }
        }""",
    """        ColourField {
            label: I18n.t("common.color");
            value: root.selected.fill;
            alpha: false;
            changed(colour) => { root.set-colour(ClipTextField.color, colour); root.commit(); }
        }

        if root.selected.karaoke: ColourField {
            label: "Palabra activa";
            value: root.selected.karaoke-color;
            alpha: false;
            changed(colour) => {
                root.set-colour(ClipTextField.karaoke-color, colour);
                root.commit();
            }
        }""")

replace("src/crates/concat/src/presets.rs",
    "        TextStyle {\n            motion: Default::default(),\n",
    "        TextStyle {\n            motion: Default::default(),\n            karaoke: None,\n")

print("Karaoke v2: one title per phrase, custom word highlight shader and editor colour picker")
