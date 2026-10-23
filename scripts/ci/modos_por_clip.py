#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Per-clip caption presentation in the ORIGINAL Concat Text inspector.

Apply after paneles_transcripcion.py. Every title keeps its own presentation
and karaoke word clocks in its serialized TextStyle. A mode switch edits only
the selected clips, without resetting their other visual properties.
"""
from pathlib import Path

MODEL="src/crates/concat-project/src/model.rs"
STUDIO="src/crates/concat/src/studio.rs"
UI="src/crates/concat/ui/timeline/model.slint"
PANEL="src/crates/concat/ui/inspector/text-panel.slint"
TITLES="src/crates/concat-host/src/titles.rs"
FX="src/crates/concat-effects/packages/concat.karaoke/effect.wgsl"
MANIFEST="src/crates/concat-effects/packages/concat.karaoke/effect.toml"

def replace(path, before, after):
    file=Path(path)
    source=file.read_text(encoding="utf-8")
    count=source.count(before)
    if count!=1:
        raise RuntimeError(f"{path}: anchor appears {count} times, expected 1: {before[:125]!r}")
    file.write_text(source.replace(before,after,1),encoding="utf-8")

# caption_mode is optional for compatibility with already-saved titles.
# None => legacy default: karaoke when its old word-clock exists, normal otherwise.
# Some(0) => Frases, Some(1) => progressive highlight, Some(2) => single active word.
replace(MODEL,
    "    pub karaoke: Option<KaraokeTrack>,\n",
    """    pub karaoke: Option<KaraokeTrack>,
    /// Presentation of this ONE clip. Serialized in the existing project.
    /// None preserves the behavior of old projects with karaoke data.
    pub caption_mode: Option<u8>,
""")
replace(MODEL,
    "        self.motion = self.motion.tidy();",
    """        self.motion = self.motion.tidy();
        self.caption_mode = self.caption_mode.filter(|mode| *mode <= 2);""")
replace(MODEL,
    "            karaoke: None,\n",
    "            karaoke: None,\n            caption_mode: None,\n")
replace("src/crates/concat/src/presets.rs",
    "            karaoke: None,\n",
    "            karaoke: None,\n            caption_mode: None,\n")

# Existing UI data flow stays intact: one tiny control in the original inspector.
replace(UI,
    "    content, font-family, color, stroke-color, background, karaoke-color,",
    "    content, font-family, color, stroke-color, background, karaoke-color, caption-mode,")
replace(UI,
    "    karaoke-color: color,\n",
    "    karaoke-color: color,\n    caption-mode: int,\n")
replace(STUDIO,
    "            karaoke: text.karaoke.is_some(),",
    """            caption_mode: text.caption_mode.map(i32::from)
                .unwrap_or(if text.karaoke.is_some() { 1 } else { 0 }),
            karaoke: text.karaoke.is_some(),""")
# No new separate panel; visual controls remain those Concat already ships.
replace(PANEL,
    "    // ── content ──────────────────────────────────────────────────────────\n",
    """    // Subtitle presentation is intrinsic to this title, not to the captions
    // generator. Switching selection reloads the value from its clip data.
    SectionBody {
        padding-left: Theme.pad;
        padding-right: Theme.pad;
        padding-top: 9px;
        padding-bottom: 7px;
        Text {
            text: "Presentación del subtítulo";
            color: Theme.fg;
            font-size: Theme.fs;
        }
        Select {
            options: ["Frases / normal", "Karaoke progresivo", "Karaoke por palabra"];
            current: root.selected.caption-mode;
            changed(index) => {
                root.set-text(ClipTextField.caption-mode,
                    index == 1 ? "1" : (index == 2 ? "2" : "0"));
                root.commit();
            }
        }
        Text {
            text: "Cada texto conserva su modo, su apariencia y sus tiempos. Karaoke requiere frases de hasta 12 palabras.";
            color: Theme.fg-muted;
            wrap: word-wrap;
            font-size: Theme.fs-sm;
        }
    }

    // ── content ──────────────────────────────────────────────────────────
""")

# clip_set_text already commits through a normal single/multiple-selection
# undoable edit. Add ONE new field to it; other text properties are unchanged.
replace(STUDIO,
    "                ClipTextField::FontFamily => text.font_family = value.to_owned(),",
    """                ClipTextField::FontFamily => text.font_family = value.to_owned(),
                ClipTextField::CaptionMode => {
                    let mode = value.parse::<u8>().unwrap_or(0).min(2);
                    text.caption_mode = Some(mode);
                    // Generate approximate word clocks only for a title that
                    // has NEVER had karaoke timing; never replace old clocks.
                    if mode != 0 && text.karaoke.is_none() {
                        let n = text.content.split_whitespace().count();
                        if n > 0 && n <= 12 {
                            let duration = clip.duration.max(1.0 / 60.0);
                            let width = duration / n as f64;
                            let words = (0..n).map(|i|
                                concat_project::model::KaraokeWord {
                                    start: i as f64 * width,
                                    end: ((i + 1) as f64 * width).min(duration),
                                }).collect();
                            text.karaoke = Some(concat_project::model::KaraokeTrack {
                                active_color: "#FFE040".to_owned(),
                                words,
                            });
                        }
                    }
                },""")

# Normal disables the shader but intentionally keeps word times and color
# in the saved clip. Both karaoke modes use the same original title and clocks.
replace(TITLES,
    "    let track = style.karaoke.as_ref()?;\n",
    """    let mode = style.caption_mode
        .unwrap_or(if style.karaoke.is_some() { 1 } else { 0 });
    if mode == 0 { return None; }
    let track = style.karaoke.as_ref()?;
""")
replace(TITLES,
    '    effect.params.insert("word_count".to_owned(), track.words.len() as f64);',
    '''    effect.params.insert("word_count".to_owned(), track.words.len() as f64);
    effect.params.insert("word_only".to_owned(), if mode == 2 { 1.0 } else { 0.0 });''')
replace(MANIFEST,
    '[[param]]\nkey = "word_count"',
    '''[[param]]
key = "word_only"
label = "Solo palabra activa"
min = 0
max = 1
default = 0
step = 1

[[param]]
key = "word_count"''')
replace(FX,
    "    word_count: f32,\n",
    "    word_only: f32,\n    word_count: f32,\n")
replace(FX,
    "    return vec4<f32>(mix(c.rgb, chosen, strength), c.a);",
    """    if (params.word_only > 0.5) {
        // The whole phrase remains one clip, but all non-active glyphs
        // are transparent. No individual title clips are generated.
        return vec4<f32>(chosen * strength, c.a * strength);
    }
    return vec4<f32>(mix(c.rgb, chosen, strength), c.a);""")

# Safeguard mode serialization independent of global caption-panel options.
replace(MODEL,
    "/// Reading with tolerance. The document reader's standing rule is that a",
    """#[cfg(test)]
mod caption_mode_per_clip_tests {
    use super::*;
    #[test]
    fn distinct_title_modes_survive_saving_and_reopening() {
        let mut normal = TextStyle::default();
        normal.content = "Buenos días".into();
        normal.caption_mode = Some(0);
        let mut karaoke = TextStyle::default();
        karaoke.content = "Quiero cantar".into();
        karaoke.caption_mode = Some(2);
        karaoke.karaoke = Some(KaraokeTrack {
            active_color: "#00BBDD".into(),
            words: vec![KaraokeWord { start: 0.0, end: 0.5 }],
        });
        let raw = serde_json::to_string(&vec![normal, karaoke]).unwrap();
        let saved: Vec<TextStyle> = serde_json::from_str(&raw).unwrap();
        assert_eq!(saved[0].caption_mode, Some(0));
        assert_eq!(saved[1].caption_mode, Some(2));
        assert_eq!(saved[1].karaoke.as_ref().unwrap().active_color, "#00BBDD");
    }

    #[test]
    fn old_projects_can_still_load_without_a_mode() {
        let text = TextStyle::default();
        let raw = serde_json::to_string(&text).unwrap();
        let old = raw.replace(r#","captionMode":null"#, "");
        let restored: TextStyle = serde_json::from_str(&old).unwrap();
        assert_eq!(restored.caption_mode, None);
    }
}

/// Reading with tolerance. The document reader's standing rule is that a""")
print("Individual clip caption modes integrated into the existing Text Inspector.")
