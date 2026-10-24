// SPDX-License-Identifier: AGPL-3.0-or-later
//! Estudio Joven's phrase editor: drafts are UI state; committed edits are
//! Concat commands, so autosave, undo, redo and the original text inspector
//! all stay in one authoritative project model.

use concat_project::{Command, commands::ClipPatch};
use crate::studio::Studio;

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Target {
    Segment { transcript_id: String, segment_id: String },
    Caption { clip_id: String },
}

#[derive(Clone, Debug)]
pub struct Entry {
    pub target: Target,
    pub label: String,
    pub content: String,
}

#[derive(Clone, Debug)]
pub enum Navigation {
    Tab(u8),
    Kind(u8),
    Select(Target),
    Close,
}

#[derive(Default)]
pub struct CaptionEditor {
    /// 0 = Generate, 1 = Edit.
    pub tab: u8,
    /// 0 = Transcription, 1 = Captions.
    pub kind: u8,
    pub selected: Option<Target>,
    pub draft: String,
    original: String,
    pub pending: Option<Navigation>,
    pub message: String,
}

impl CaptionEditor {
    pub fn dirty(&self) -> bool {
        self.selected.is_some() && self.draft != self.original
    }

    /// Stable IDs, not row numbers, identify edits. Rows may reorder after
    /// a clip is trimmed, or when a new Whisper pass adds another transcript.
    pub fn entries(&self, studio: &Studio) -> Vec<Entry> {
        let timeline = studio.timeline();
        if self.kind == 0 {
            let mut rows = Vec::new();
            for transcript in studio.project().transcripts().into_iter()
                .filter(|transcript| transcript.timeline_id == timeline.id)
            {
                for segment in transcript.segments {
                    rows.push(Entry {
                        target: Target::Segment {
                            transcript_id: transcript.id.clone(),
                            segment_id: segment.id.clone(),
                        },
                        label: format!("{:.2}s  {}", segment.start, brief(&segment.text)),
                        content: segment.text,
                    });
                }
            }
            rows
        } else {
            let mut clips: Vec<_> = timeline.clips.iter()
                .filter(|clip| clip.caption_metadata().is_some())
                .collect();
            clips.sort_by(|a, b| a.start.total_cmp(&b.start));
            clips.into_iter().map(|clip| {
                let content = clip.text.as_ref()
                    .map(|text| text.content.clone()).unwrap_or_default();
                Entry {
                    target: Target::Caption { clip_id: clip.id.clone() },
                    label: format!("{:.2}s  {}", clip.start, brief(&content)),
                    content,
                }
            }).collect()
        }
    }

    pub fn selected_index(&self, studio: &Studio) -> i32 {
        self.entries(studio).iter().position(|entry| Some(&entry.target) == self.selected.as_ref())
            .map(|i| i as i32).unwrap_or(-1)
    }

    pub fn ensure_selection(&mut self, studio: &mut Studio) {
        if self.tab != 1 || self.selected_index(studio) >= 0 {
            return;
        }
        self.selected = None;
        self.draft.clear();
        self.original.clear();
        if let Some(first) = self.entries(studio).into_iter().next() {
            self.commit_target(studio, first);
        }
    }

    pub fn navigate(&mut self, studio: &mut Studio, next: Navigation) -> bool {
        if self.dirty() {
            self.pending = Some(next);
            return false;
        }
        self.perform_navigation(studio, next)
    }

    /// Handles a previously requested selection/tab change. Returning true
    /// asks the caller to close the window after Apply/Discard.
    pub fn resolve(&mut self, studio: &mut Studio, apply: bool) -> bool {
        if apply && !self.apply(studio) {
            return false;
        }
        if !apply {
            self.draft = self.original.clone();
            self.message.clear();
        }
        let next = self.pending.take();
        next.is_some_and(|next| self.perform_navigation(studio, next))
    }

    fn perform_navigation(&mut self, studio: &mut Studio, next: Navigation) -> bool {
        self.message.clear();
        match next {
            Navigation::Tab(tab) => {
                self.tab = tab.min(1);
                self.ensure_selection(studio);
            }
            Navigation::Kind(kind) => {
                self.kind = kind.min(1);
                self.selected = None;
                self.draft.clear();
                self.original.clear();
                self.ensure_selection(studio);
            }
            Navigation::Select(target) => {
                let match_entry = self.entries(studio).into_iter()
                    .find(|entry| entry.target == target);
                if let Some(entry) = match_entry { self.commit_target(studio, entry); }
            }
            Navigation::Close => return true,
        }
        false
    }

    fn commit_target(&mut self, studio: &mut Studio, entry: Entry) {
        if let Target::Caption { clip_id } = &entry.target {
            studio.focus_caption_clip(clip_id);
        }
        self.selected = Some(entry.target);
        self.original = entry.content.clone();
        self.draft = entry.content;
        self.message.clear();
    }

    pub fn discard(&mut self) {
        self.draft = self.original.clone();
        self.message.clear();
    }

    pub fn apply(&mut self, studio: &mut Studio) -> bool {
        if !self.dirty() {
            return true;
        }
        let next_text = self.draft.trim().to_owned();
        if next_text.is_empty() {
            self.message = "El texto no puede quedar vacío.".into();
            return false;
        }
        let Some(target) = self.selected.clone() else { return false; };
        let mut commands = Vec::new();
        match target {
            Target::Caption { clip_id } => {
                let Some(clip) = studio.clip(&clip_id) else {
                    self.message = "El subtítulo ya no existe.".into();
                    return false;
                };
                if clip.caption_metadata().is_none() {
                    self.message = "El texto seleccionado ya no es un subtítulo.".into();
                    return false;
                }
                let Some(mut style) = clip.text.clone() else { return false; };
                if style.content != self.original {
                    self.message = "Este subtítulo cambió. Descarta el borrador y vuelve a abrirlo.".into();
                    return false;
                }
                style.content = next_text.clone();
                commands.push(Command::UpdateClip {
                    clip_id, patch: ClipPatch {
                        text: Some(Some(style)), ..ClipPatch::default()
                    },
                });
            }
            Target::Segment { transcript_id, segment_id } => {
                let Some(mut transcript) = studio.project().transcript(&transcript_id) else {
                    self.message = "La transcripción ya no existe.".into();
                    return false;
                };
                let Some(segment) = transcript.segments.iter_mut()
                    .find(|segment| segment.id == segment_id) else {
                    self.message = "La frase ya no existe.".into();
                    return false;
                };
                if segment.text != self.original {
                    self.message = "La frase cambió en otro lugar. Descarta y vuelve a seleccionarla.".into();
                    return false;
                }
                segment.text = next_text.clone();
                commands.push(Command::UpsertTranscript { transcript });
                // Update the caption only when it still matches the old
                // recognised phrase. Individual changes from the original
                // text inspector take precedence over later transcript edits.
                for clip in &studio.timeline().clips {
                    let Some(meta) = clip.caption_metadata() else { continue; };
                    if meta.transcript_id.as_deref() != Some(transcript_id.as_str())
                        || meta.segment_id.as_deref() != Some(segment_id.as_str())
                    {
                        continue;
                    }
                    let Some(mut style) = clip.text.clone() else { continue; };
                    if style.content != self.original { continue; }
                    style.content = next_text.clone();
                    commands.push(Command::UpdateClip {
                        clip_id: clip.id.clone(),
                        patch: ClipPatch {
                            text: Some(Some(style)), ..ClipPatch::default()
                        },
                    });
                }
            }
        }
        studio.apply(Command::Batch { commands });
        self.original = next_text.clone();
        self.draft = next_text;
        self.message.clear();
        true
    }
}

fn brief(text: &str) -> String {
    let one_line = text.split_whitespace().collect::<Vec<_>>().join(" ");
    let mut chars = one_line.chars();
    let short: String = chars.by_ref().take(48).collect();
    if chars.next().is_some() { format!("{short}…") } else { short }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn changing_one_draft_is_detected_without_changing_its_original() {
        let mut editor = CaptionEditor::default();
        editor.selected = Some(Target::Caption { clip_id: "c1".into() });
        editor.original = "Primero".into();
        editor.draft = "Corregido".into();
        assert!(editor.dirty());
        editor.draft = "Primero".into();
        assert!(!editor.dirty());
    }
    #[test]
    fn labels_avoid_extremely_long_rows() {
        let label = brief(&"Hola ".repeat(100));
        assert!(label.chars().count() <= 49);
    }
}
