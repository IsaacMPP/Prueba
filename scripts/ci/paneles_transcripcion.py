#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Estudio Joven: separated transcript/caption views using Concat's OWN text inspector.

Apply after transcripcion_primero.py. Assert anchors to fail loudly when upstream changes.
This increment adds scrollable, independently editable transcript segments, caption rows
that select real timeline clips, and removes duplicate font/color controls from the
caption-generation screen. It deliberately DOES NOT replace the existing text inspector.
"""
from pathlib import Path

CAP = "src/crates/concat/src/panes/captions.rs"
DIALOG = "src/crates/concat/ui/dialogs/captions.slint"
APP = "src/crates/concat/ui/app.slint"
LIB = "src/crates/concat/src/lib.rs"

def replace(path, before, after):
    file = Path(path)
    body = file.read_text(encoding="utf-8")
    count = body.count(before)
    if count != 1:
        raise RuntimeError(f"{path}: anchor expected once; found {count}: {before[:110]!r}")
    file.write_text(body.replace(before, after, 1), encoding="utf-8")

# The two views share a single caption workspace, but never duplicate the
# existing Text Inspector's appearance controls.
replace(DIALOG, "export struct CaptionsSheetData {",
"""export struct TranscriptItemData {
    index: int,
    start: string,
    end: string,
    content: string,
}

export struct SubtitleItemData {
    clip-id: string,
    start: string,
    end: string,
    content: string,
}

export struct CaptionsSheetData {""")
replace(DIALOG, "    has-transcript: bool,\n",
"""    has-transcript: bool,
    transcript-rows: [TranscriptItemData],
    subtitle-rows: [SubtitleItemData],
""")
replace(DIALOG, "    callback transcribe();\n",
"""    callback transcribe();
    callback segment-selected(index: int);
    callback segment-edited(index: int, text: string);
    callback subtitle-selected(id: string);
""")
replace(DIALOG, "    property <bool> from-voice: root.data.from-voice;\n",
"""    property <bool> from-voice: root.data.from-voice;
    property <int> view: 0; // 0 = transcripción; 1 = subtítulos
    property <int> selected-segment: -1;
    property <string> segment-draft: "";
""")
replace(DIALOG, "    surface-width: 480px;\n", "    surface-width: 620px;\n")
replace(DIALOG,
    "    VerticalLayout {\n        if !root.data.running && (!root.from-voice || root.data.has-transcript): DialogSection {",
    """    VerticalLayout {
        HorizontalLayout {
            padding-left: 14px;
            padding-right: 14px;
            padding-top: 12px;
            padding-bottom: 8px;
            SegmentedControl {
                options: ["Transcripción", "Subtítulos"];
                current: root.view;
                changed(index) => { root.view = index; }
            }
        }

        if !root.data.running && root.view == 0 && !root.from-voice: DialogSection {""")
replace(DIALOG,
    "        if !root.data.running && root.from-voice: DialogSection {",
    "        if !root.data.running && root.view == 0 && root.from-voice: DialogSection {")
# Insert the scrollable transcript list immediately above the Voice source section.
replace(DIALOG,
    "        if !root.data.running && root.view == 0 && root.from-voice: DialogSection {",
    """        if !root.data.running && root.view == 0 && root.data.has-transcript && root.from-voice: DialogSection {
            title: "Transcripción corregible";
            Text {
                text: "Selecciona una frase para corregirla; los tiempos se conservan. Cambiar las palabras puede requerir realineación.";
                color: Theme.fg-muted;
                font-size: Theme.fs-sm;
                wrap: word-wrap;
            }
            Flickable {
                height: 246px;
                content-height: root.data.transcript-rows.length * 65px;
                VerticalLayout {
                    alignment: start;
                    spacing: 3px;
                    for item[index] in root.data.transcript-rows: Rectangle {
                        height: 62px;
                        background: root.selected-segment == index ? Theme.accent-soft : Theme.well;
                        border-radius: Theme.r-sm;
                        HorizontalLayout {
                            padding: 8px;
                            spacing: 10px;
                            VerticalLayout {
                                width: 122px;
                                spacing: 2px;
                                Text { text: item.start; color: Theme.fg-dim; font-family: Theme.font-technical; font-size: Theme.fs-sm; }
                                Text { text: item.end; color: Theme.fg-dim; font-family: Theme.font-technical; font-size: Theme.fs-sm; }
                            }
                            Text {
                                text: item.content;
                                horizontal-stretch: 1;
                                wrap: word-wrap;
                                color: Theme.fg;
                                font-size: Theme.fs;
                                vertical-alignment: center;
                                overflow: elide;
                            }
                        }
                        pick := TouchArea {
                            mouse-cursor: pointer;
                            clicked => {
                                root.selected-segment = index;
                                root.segment-draft = item.content;
                                root.segment-selected(index);
                            }
                        }
                    }
                }
            }
            if root.selected-segment >= 0: Rectangle {
                height: 92px;
                background: Theme.well;
                border-radius: Theme.r;
                border-width: 1px;
                border-color: Theme.line;
                TextInput {
                    x: 9px;
                    y: 7px;
                    width: parent.width - 18px;
                    height: parent.height - 14px;
                    text <=> root.segment-draft;
                    color: Theme.fg;
                    font-size: Theme.fs-lg;
                    single-line: false;
                    wrap: word-wrap;
                    edited => { root.segment-edited(root.selected-segment, self.text); }
                }
            }
        }

        if !root.data.running && root.view == 0 && root.from-voice: DialogSection {""")
replace(DIALOG, "        if !root.data.running: DialogSection {\n            title: I18n.t(\"captions.captions\");",
"""        if !root.data.running && root.view == 1: DialogSection {
            title: "Creación de subtítulos";""")
# No duplicate colour or font selectors. Titles and captions already use the
# selected timeline text clip's existing inspector; leave appearance there.
replace(DIALOG,
"""            DialogRow {
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

""", "")
replace(DIALOG,
    """                text: "Una palabra por clip, editable en Texto. Para cambiar a una fuente importada, usa Texto > Usar para nuevos titulos y elige Estilo guardado. Los tiempos sin alineacion exacta son aproximados.";""",
    """                text: "Selecciona un subtítulo en la lista inferior para modificar fuente, color, tamaño, sombra y animaciones en el inspector Texto que ya existe. Las marcas de palabra sin alineación exacta son estimaciones.";""")
# Add scrollable subtitle list above footer action buttons.
replace(DIALOG,
    "        Rectangle {\n            height: 1px;\n            background: Theme.line;\n        }\n\n        VerticalLayout {",
    """        if root.view == 1: DialogSection {
            title: "Subtítulos en la línea de tiempo";
            if root.data.subtitle-rows.length == 0: Text {
                text: "No hay subtítulos. Corrige la transcripción y pulsa Generar subtítulos.";
                color: Theme.fg-muted;
                wrap: word-wrap;
                font-size: Theme.fs-sm;
            }
            Flickable {
                height: 242px;
                content-height: root.data.subtitle-rows.length * 65px;
                VerticalLayout {
                    alignment: start;
                    spacing: 3px;
                    for item[index] in root.data.subtitle-rows: Rectangle {
                        height: 62px;
                        border-radius: Theme.r-sm;
                        background: Theme.well;
                        HorizontalLayout {
                            padding: 8px;
                            spacing: 10px;
                            VerticalLayout {
                                width: 122px;
                                spacing: 2px;
                                Text { text: item.start; color: Theme.fg-dim; font-family: Theme.font-technical; font-size: Theme.fs-sm; }
                                Text { text: item.end; color: Theme.fg-dim; font-family: Theme.font-technical; font-size: Theme.fs-sm; }
                            }
                            Text {
                                text: item.content;
                                horizontal-stretch: 1;
                                wrap: word-wrap;
                                color: Theme.fg;
                                font-size: Theme.fs;
                                vertical-alignment: center;
                                overflow: elide;
                            }
                        }
                        pick := TouchArea {
                            mouse-cursor: pointer;
                            clicked => { root.subtitle-selected(item.clip-id); }
                        }
                    }
                }
            }
            Text {
                text: "Clic: seleccionar el clip en la línea de tiempo y editarlo con el inspector Texto existente.";
                color: Theme.fg-muted;
                font-size: Theme.fs-sm;
                wrap: word-wrap;
            }
        }

        Rectangle {
            height: 1px;
            background: Theme.line;
        }

        VerticalLayout {""")
# The primary action is shown only on the relevant view: separate speech
# recognition from caption generation without retranscription.
replace(DIALOG,
    '                label: root.from-voice ? (root.data.has-transcript ? "2. Generar subtítulos" : "1. Transcribir voz") : I18n.t("captions.addCaptions");',
    '                label: root.from-voice ? (root.view == 0 ? "Transcribir voz" : "Crear subtítulos") : I18n.t("captions.addCaptions");')
replace(DIALOG,
    "                clicked => { root.begin(); }\n",
    """                clicked => {
                    if root.from-voice && root.view == 0 { root.transcribe(); }
                    else { root.begin(); }
                }
""")
replace(DIALOG,
    "                enabled: root.from-voice ? root.data.ready && root.data.source >= 0 : root.draft != \"\";",
    '                enabled: root.from-voice ? (root.view == 0 ? root.data.ready && root.data.source >= 0 : root.data.has-transcript) : root.draft != "";')
replace(DIALOG, "            if !root.data.running && root.from-voice && root.data.has-transcript: Button {",
    "            if !root.data.running && root.view == 0 && root.from-voice && root.data.has-transcript: Button {")
# Buttons still share status/progress footer; subtitle SRT I/O is on subtitle view.
replace(DIALOG,
    "            if !root.data.running: HorizontalLayout {\n                spacing: 8px;\n\n                Button {",
    "            if !root.data.running && root.view == 1: HorizontalLayout {\n                spacing: 8px;\n\n                Button {")
# expose new data and callbacks through App's existing dialog bridge.
replace(APP, 'import { CaptionsDialog, CaptionsSheetData } from "dialogs/captions.slint";',
    'import { CaptionsDialog, CaptionsSheetData, TranscriptItemData, SubtitleItemData } from "dialogs/captions.slint";')
replace(APP, "    CaptionsSheetData, SpeechSheetData, VoiceoverData,",
    "    CaptionsSheetData, TranscriptItemData, SubtitleItemData, SpeechSheetData, VoiceoverData,")
replace(APP, "    callback captions-transcribe();\n",
"""    callback captions-transcribe();
    callback captions-segment-selected(index: int);
    callback captions-segment-edited(index: int, text: string);
    callback captions-subtitle-selected(id: string);
""")
replace(APP, "            transcribe => { root.captions-transcribe(); }\n",
"""            transcribe => { root.captions-transcribe(); }
            segment-selected(index) => { root.captions-segment-selected(index); }
            segment-edited(index, text) => { root.captions-segment-edited(index, text); }
            subtitle-selected(id) => { root.captions-subtitle-selected(id); }
""")
replace(LIB, "    app.on_captions_transcribe(on_window!(|state| {\n",
"""    app.on_captions_segment_selected(on_window!(|state, index: i32| {
        state.handle(Msg::Captions(CaptionsMsg::SegmentSelected(index)));
    }));
    app.on_captions_segment_edited(on_window!(|state, index: i32, value: SharedString| {
        state.handle(Msg::Captions(CaptionsMsg::SegmentEdited(index, value.to_string())));
    }));
    app.on_captions_subtitle_selected(on_window!(|state, id: SharedString| {
        state.handle(Msg::Captions(CaptionsMsg::SubtitleSelected(id.to_string())));
    }));
    app.on_captions_transcribe(on_window!(|state| {
""")
# Model selection: don't create or modify appearance controls. Selecting
# a subtitle changes Studio.selection -> old SelectedClipData/Text Inspector.
replace(CAP, "use crate::ui::CaptionsSheetData;",
    "use crate::ui::{CaptionsSheetData, TranscriptItemData, SubtitleItemData};")
replace(CAP, "    Transcribe,\n",
"""    Transcribe,
    SegmentSelected(i32),
    SegmentEdited(i32, String),
    SubtitleSelected(String),
""")
replace(CAP, "            CaptionsMsg::Transcribe => self.run_sound(studio),\n",
"""            CaptionsMsg::Transcribe => self.run_sound(studio),
            CaptionsMsg::SegmentSelected(index) => {
                if let Some(voice) = &self.cached_voice {
                    if let Some(segment) = usize::try_from(index).ok().and_then(|i| voice.segments.get(i)) {
                        studio.seek((voice.subject.start + segment.start / voice.subject.speed) as f32);
                    }
                }
            }
            CaptionsMsg::SegmentEdited(index, value) => {
                if let Some(voice) = &mut self.cached_voice {
                    if let Some(segment) = usize::try_from(index).ok().and_then(|i| voice.segments.get_mut(i)) {
                        if segment.text != value {
                            let replacements: Vec<String> = value.split_whitespace().map(str::to_owned).collect();
                            if replacements.len() == segment.words.len() {
                                for (word, replacement) in segment.words.iter_mut().zip(replacements) {
                                    word.text = replacement;
                                }
                            } else {
                                segment.words.clear();
                                self.message = "Cambió la segmentación; los tiempos por palabra serán aproximados.".into();
                            }
                            segment.text = value;
                            self.text = voice.segments.iter().map(|s| s.text.trim())
                                .filter(|s| !s.is_empty()).collect::<Vec<_>>().join(" ");
                            voice.original_text = self.text.clone();
                        }
                    }
                }
            }
            CaptionsMsg::SubtitleSelected(id) => {
                if let Some(at) = studio.clip(&id).filter(|clip| clip.kind == ClipKind::Text).map(|clip| clip.start) {
                    studio.flush_commit();
                    studio.selection = vec![id];
                    studio.transition_selected = None;
                    studio.seek(at as f32);
                }
            }
""")
replace(CAP,
    "        CaptionsSheetData {\n",
"""        let transcript_rows: Vec<TranscriptItemData> = self.cached_voice.as_ref()
            .map(|voice| voice.segments.iter().enumerate().map(|(index, segment)| {
                TranscriptItemData {
                    index: index as i32,
                    start: format_caption_clock(voice.subject.start + segment.start / voice.subject.speed).into(),
                    end: format_caption_clock(voice.subject.start + segment.end / voice.subject.speed).into(),
                    content: segment.text.as_str().into(),
                }
            }).collect()).unwrap_or_default();
        let mut subtitle_rows: Vec<(f64, SubtitleItemData)> = studio.timeline().clips.iter()
            .filter(|clip| clip.kind == ClipKind::Text)
            .filter_map(|clip| Some((clip.start, SubtitleItemData {
                clip_id: clip.id.as_str().into(),
                start: format_caption_clock(clip.start).into(),
                end: format_caption_clock(clip.start + clip.duration).into(),
                content: clip.text.as_ref()?.content.as_str().into(),
            }))).collect();
        subtitle_rows.sort_by(|a, b| a.0.total_cmp(&b.0));
        CaptionsSheetData {
            transcript_rows: std::rc::Rc::new(slint::VecModel::from(transcript_rows)).into(),
            subtitle_rows: std::rc::Rc::new(slint::VecModel::from(
                subtitle_rows.into_iter().map(|(_, row)| row).collect::<Vec<_>>()
            )).into(),
""")
replace(CAP,
    "/// Imported cues keep the file's timing, including captions shorter than",
"""/// Timeline time, displayed using the same absolute timebase for both panes.
fn format_caption_clock(seconds: f64) -> String {
    let frames = (seconds.max(0.0) * 100.0).round() as u64;
    format!("{:02}:{:02}:{:02}.{:02}", frames / 360_000,
        frames / 6_000 % 60, frames / 100 % 60, frames % 100)
}

/// Imported cues keep the file's timing, including captions shorter than""")
# Reuse existing multi-clip text controls for entire caption tracks:
# one selection from the Subtítulos pane, then edit appearance in Text Inspector.
replace(DIALOG, "    callback subtitle-selected(id: string);\n",
"""    callback subtitle-selected(id: string);
    callback subtitle-track-selected();
""")
replace(DIALOG,
    """            Text {
                text: "Clic: seleccionar el clip en la línea de tiempo y editarlo con el inspector Texto existente.";
                color: Theme.fg-muted;
                font-size: Theme.fs-sm;
                wrap: word-wrap;
            }
        }""",
    """            Button {
                block: true;
                ghost: true;
                label: "Seleccionar todos los subtítulos de la pista";
                clicked => { root.subtitle-track-selected(); }
            }
            Text {
                text: "Usa el inspector Texto existente para cambiar fuente, color, tamaño y otros atributos de toda la selección.";
                color: Theme.fg-muted;
                font-size: Theme.fs-sm;
                wrap: word-wrap;
            }
        }""")
replace(APP, "    callback captions-subtitle-selected(id: string);\n",
"""    callback captions-subtitle-selected(id: string);
    callback captions-subtitle-track-selected();
""")
replace(APP, "            subtitle-selected(id) => { root.captions-subtitle-selected(id); }\n",
"""            subtitle-selected(id) => { root.captions-subtitle-selected(id); }
            subtitle-track-selected => { root.captions-subtitle-track-selected(); }
""")
replace(LIB,
    "    app.on_captions_subtitle_selected(on_window!(|state, id: SharedString| {\n",
"""    app.on_captions_subtitle_track_selected(on_window!(|state| {
        state.handle(Msg::Captions(CaptionsMsg::SubtitleTrackSelected));
    }));
    app.on_captions_subtitle_selected(on_window!(|state, id: SharedString| {
""")
replace(CAP, "    SubtitleSelected(String),\n",
"""    SubtitleSelected(String),
    SubtitleTrackSelected,
""")
replace(CAP, "            CaptionsMsg::SubtitleSelected(id) => {\n",
"""            CaptionsMsg::SubtitleTrackSelected => {
                let track = studio.sole_selection()
                    .and_then(|id| studio.clip(&id).filter(|c| c.kind == ClipKind::Text)
                        .map(|clip| clip.track_id.clone()))
                    .or_else(|| srt::busiest_title_lane(studio.timeline()));
                if let Some(track) = track {
                    let ids: Vec<String> = studio.timeline().clips.iter()
                        .filter(|clip| clip.kind == ClipKind::Text && clip.track_id == track)
                        .map(|clip| clip.id.clone()).collect();
                    if !ids.is_empty() {
                        studio.flush_commit();
                        studio.selection = ids;
                        studio.transition_selected = None;
                    }
                }
            }
            CaptionsMsg::SubtitleSelected(id) => {
""")

print("Estudio Joven: transcript / captions scroll panes; existing Text Inspector retained.")
