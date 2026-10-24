// SPDX-License-Identifier: AGPL-3.0-or-later
//! Typed, persistent subtitle identity and transcriptions for Estudio Joven.
//! Stored in the existing tolerant Project/Clip extra fields to preserve
//! backward compatibility without duplicating Concat's original text editor.

use std::collections::HashSet;
use serde::{Deserialize, Serialize};
use serde_json::{from_value, to_value};
use crate::model::{Clip, ClipKind, Project, Timeline};
use crate::srt;

const TRANSCRIPTS: &str = "estudioJovenTranscripts";
const CAPTION: &str = "estudioJovenCaption";

#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TranscriptWord {
    pub id: String,
    pub text: String,
    pub start: f64,
    pub end: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub speaker_id: Option<String>,
}

#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TranscriptSegment {
    pub id: String,
    pub text: String,
    pub start: f64,
    pub end: f64,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub words: Vec<TranscriptWord>,
}

/// Times are seconds relative to the source clip, not the project timeline.
#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TranscriptDocument {
    pub id: String,
    pub timeline_id: String,
    pub source_clip_id: String,
    #[serde(default)]
    pub language: String,
    #[serde(default)]
    pub segments: Vec<TranscriptSegment>,
}

impl TranscriptDocument {
    pub fn valid(&self) -> bool {
        if self.id.trim().is_empty() || self.timeline_id.trim().is_empty()
            || self.source_clip_id.trim().is_empty() { return false; }
        let mut seen_segments = HashSet::new();
        for seg in &self.segments {
            if seg.id.trim().is_empty() || !seen_segments.insert(seg.id.as_str())
                || !interval(seg.start, seg.end) { return false; }
            let mut seen_words = HashSet::new();
            let mut previous = seg.start;
            for word in &seg.words {
                if word.id.trim().is_empty() || !seen_words.insert(word.id.as_str())
                    || !interval(word.start, word.end)
                    || word.start < seg.start || word.end > seg.end
                    || word.start < previous { return false; }
                previous = word.start;
            }
        }
        true
    }
}

#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub enum CaptionPresentation {
    #[default]
    Normal,
    KaraokeProgressive,
    KaraokeWord,
}

/// Seconds relative to the subtitle clip, independently from transcript clocks.
#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CaptionWord {
    pub id: String,
    pub start: f64,
    pub end: f64,
}

/// Explicit metadata: a normal title has no CaptionMetadata at all.
/// The original Clip.text/TextStyle owns font, size, color and animations.
#[cfg_attr(feature = "schema", derive(schemars::JsonSchema))]
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CaptionMetadata {
    #[serde(default)]
    pub presentation: CaptionPresentation,
    #[serde(default = "default_active_color")]
    pub active_color: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub words: Vec<CaptionWord>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub transcript_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub segment_id: Option<String>,
}

impl Default for CaptionMetadata {
    fn default() -> Self {
        Self {
            presentation: CaptionPresentation::Normal,
            active_color: default_active_color(),
            words: Vec::new(),
            transcript_id: None,
            segment_id: None,
        }
    }
}

impl CaptionMetadata {
    /// Metadata identity must survive a later trim: trimming a clip can
    /// shorten it before the karaoke clocks are realigned in the editor.
    pub fn valid(&self) -> bool {
        let color_ok = self.active_color.strip_prefix('#')
            .is_some_and(|hex| hex.len() == 6 && hex.bytes().all(|c| c.is_ascii_hexdigit()));
        if !color_ok { return false; }
        let mut seen = HashSet::new();
        let mut previous = 0.0;
        for word in &self.words {
            if word.id.trim().is_empty() || !seen.insert(word.id.as_str())
                || !interval(word.start, word.end) || word.start < previous
            {
                return false;
            }
            previous = word.start;
        }
        true
    }

    /// New metadata must fit the clip; existing metadata remains readable
    /// after trimming so subtitle classification cannot disappear silently.
    pub fn valid_for_clip(&self, duration: f64) -> bool {
        self.valid() && duration.is_finite() && duration > 0.0
            && self.words.iter().all(|word| word.end <= duration + 0.000001)
    }
}

fn default_active_color() -> String { "#FFE040".into() }
fn interval(a: f64, b: f64) -> bool { a.is_finite() && b.is_finite() && a >= 0.0 && b > a }

impl Clip {
    pub fn caption_metadata(&self) -> Option<CaptionMetadata> {
        if self.kind != ClipKind::Text { return None; }
        let meta = from_value::<CaptionMetadata>(self.extra.get(CAPTION)?.clone()).ok()?;
        meta.valid().then_some(meta)
    }

    pub(crate) fn set_caption_metadata(&mut self, meta: Option<CaptionMetadata>) -> bool {
        let next = meta.map(|m| to_value(m).expect("caption serializes"));
        if self.extra.get(CAPTION) == next.as_ref() { return false; }
        if let Some(value) = next { self.extra.insert(CAPTION.into(), value); }
        else { self.extra.remove(CAPTION); }
        true
    }
}

impl Project {
    pub fn transcripts(&self) -> Vec<TranscriptDocument> {
        self.extra.get(TRANSCRIPTS).cloned()
            .and_then(|raw| from_value::<Vec<TranscriptDocument>>(raw).ok())
            .unwrap_or_default().into_iter().filter(TranscriptDocument::valid).collect()
    }

    pub fn transcript(&self, id: &str) -> Option<TranscriptDocument> {
        self.transcripts().into_iter().find(|item| item.id == id)
    }

    pub fn caption_clip_ids(&self, timeline_id: &str) -> Vec<String> {
        self.timelines.iter().find(|timeline| timeline.id == timeline_id)
            .into_iter().flat_map(|timeline| timeline.clips.iter())
            .filter(|clip| clip.caption_metadata().is_some())
            .map(|clip| clip.id.clone()).collect()
    }

    pub(crate) fn upsert_transcript(&mut self, transcript: TranscriptDocument) -> bool {
        let mut items = self.transcripts();
        if let Some(item) = items.iter_mut().find(|item| item.id == transcript.id) {
            if *item == transcript { return false; }
            *item = transcript;
        } else { items.push(transcript); }
        self.extra.insert(TRANSCRIPTS.into(), to_value(items).expect("transcripts serialize"));
        true
    }

    pub(crate) fn remove_transcript(&mut self, id: &str) -> bool {
        let mut items = self.transcripts();
        let previous = items.len();
        items.retain(|item| item.id != id);
        if previous == items.len() { return false; }
        if items.is_empty() { self.extra.remove(TRANSCRIPTS); }
        else { self.extra.insert(TRANSCRIPTS.into(), to_value(items).expect("transcripts serialize")); }
        true
    }
}

/// Export only explicitly identified subtitle clips, never regular titles.
pub fn caption_cues(timeline: &Timeline, track_id: Option<&str>) -> Vec<srt::Cue> {
    let mut cues: Vec<srt::Cue> = timeline.clips.iter()
        .filter(|clip| clip.caption_metadata().is_some()
            && track_id.is_none_or(|id| clip.track_id == id))
        .filter_map(|clip| {
            let text = clip.text.as_ref()?.content.trim();
            (!text.is_empty()).then(|| srt::Cue {
                start: clip.start,
                end: clip.start + clip.duration,
                text: text.to_owned(),
            })
        })
        .collect();
    cues.sort_by(|a, b| a.start.total_cmp(&b.start));
    cues
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::commands::Command;
    use crate::doc::{DocumentSettings, from_document, to_document};
    use crate::editor::Editor;
    use crate::model::TextStyle;

    fn settings() -> DocumentSettings {
        DocumentSettings { name: "Estudio Joven".into(), width: 1920,
            height: 1080, rate_num: 30, rate_den: 1 }
    }

    fn transcript() -> TranscriptDocument {
        TranscriptDocument {
            id: "tx1".into(), timeline_id: "TL1".into(),
            source_clip_id: "source7".into(), language: "es".into(),
            segments: vec![TranscriptSegment {
                id: "seg1".into(), text: "Hola mundo".into(),
                start: 0.2, end: 1.0,
                words: vec![
                    TranscriptWord { id: "w1".into(), text: "Hola".into(),
                        start: 0.2, end: 0.5, speaker_id: None },
                    TranscriptWord { id: "w2".into(), text: "mundo".into(),
                        start: 0.5, end: 1.0, speaker_id: None }
                ],
            }],
        }
    }

    #[test]
    fn transcription_roundtrip_undo_and_redo() {
        let mut editor = Editor::new();
        let tx = transcript();
        assert!(editor.apply(Command::UpsertTranscript { transcript: tx.clone() }).unwrap().applied);
        assert_eq!(editor.project().transcript("tx1"), Some(tx.clone()));
        assert!(editor.undo());
        assert!(editor.project().transcripts().is_empty());
        assert!(editor.redo());
        let document = to_document(&settings(), editor.project());
        assert_eq!(from_document(&document).unwrap().transcript("tx1"), Some(tx));
    }

    #[test]
    fn each_text_preserves_its_mode_and_word_times() {
        let mut editor = Editor::new();
        let make = |text: &str| Command::AddTextClip {
            track_id: Some("T1".into()), above: false, start: 0.0,
            style: Some(TextStyle { content: text.into(), ..TextStyle::default() }),
            duration: Some(2.0), offset_y: None,
        };
        let a = editor.apply(make("Primero")).unwrap().created_id.unwrap();
        let b = editor.apply(make("Segundo")).unwrap().created_id.unwrap();
        let mut meta = CaptionMetadata {
            presentation: CaptionPresentation::KaraokeProgressive,
            active_color: "#11AABB".into(),
            words: vec![CaptionWord { id: "word1".into(), start: 0.1, end: 0.7 }],
            ..CaptionMetadata::default()
        };
        editor.apply(Command::SetCaptionMetadata { clip_id: a.clone(), metadata: Some(meta.clone()) }).unwrap();
        editor.apply(Command::SetCaptionMetadata { clip_id: b.clone(), metadata: Some(CaptionMetadata::default()) }).unwrap();
        meta.presentation = CaptionPresentation::Normal;
        editor.apply(Command::SetCaptionMetadata { clip_id: a.clone(), metadata: Some(meta.clone()) }).unwrap();
        let reloaded = from_document(&to_document(&settings(), editor.project())).unwrap();
        let first = reloaded.active().clips.iter().find(|clip| clip.id == a).unwrap();
        let second = reloaded.active().clips.iter().find(|clip| clip.id == b).unwrap();
        assert_eq!(first.caption_metadata(), Some(meta));
        assert_eq!(second.caption_metadata().unwrap().presentation, CaptionPresentation::Normal);
        assert_eq!(reloaded.caption_clip_ids("TL1").len(), 2);
        assert_eq!(first.caption_metadata().unwrap().words.len(), 1);
    }

    #[test]
    fn ordinary_title_remains_excluded_and_invalid_metadata_rejected() {
        let mut editor = Editor::new();
        let id = editor.apply(Command::AddTextClip {
            track_id: Some("T1".into()), above: false, start: 0.0,
            style: None, duration: Some(2.0), offset_y: None,
        }).unwrap().created_id.unwrap();
        assert!(editor.project().caption_clip_ids("TL1").is_empty());
        assert!(editor.apply(Command::SetCaptionMetadata {
            clip_id: id,
            metadata: Some(CaptionMetadata { active_color: "wrong".into(),
                ..CaptionMetadata::default() }),
        }).is_err());
        assert!(editor.project().caption_clip_ids("TL1").is_empty());
    }

    #[test]
    fn trimming_a_caption_never_makes_its_identity_disappear() {
        use crate::commands::TrimEdge;
        let mut editor = Editor::new();
        let id = editor.apply(Command::AddCaptionClip {
            track_id: Some("T1".into()), above: false, start: 0.5,
            style: Some(TextStyle {
                content: "Texto".into(), ..TextStyle::default()
            }), duration: Some(2.0), offset_y: None,
            metadata: CaptionMetadata {
                words: vec![CaptionWord {
                    id: "w1".into(), start: 1.0, end: 1.8
                }],
                ..CaptionMetadata::default()
            },
        }).unwrap().created_id.unwrap();
        editor.apply(Command::TrimClip {
            clip_id: id.clone(), edge: TrimEdge::End, delta: -1.3, ripple: false,
        }).unwrap();
        let clip = editor.project().active().clips.iter()
            .find(|clip| clip.id == id).unwrap();
        assert!(clip.duration < 1.8);
        assert!(clip.caption_metadata().is_some(),
            "classification survives until word timings are adjusted");
        assert_eq!(editor.project().caption_clip_ids("TL1").len(), 1);
    }

    #[test]
    fn exporting_only_real_subtitles_excludes_titles_on_same_track() {
        let mut editor = Editor::new();
        editor.apply(Command::AddCaptionClip {
            track_id: Some("T1".into()), above: false, start: 0.5,
            style: Some(TextStyle { content: "Subtítulo".into(), ..TextStyle::default() }),
            duration: Some(1.0), offset_y: None,
            metadata: CaptionMetadata::default(),
        }).unwrap();
        editor.apply(Command::AddTextClip {
            track_id: Some("T1".into()), above: false, start: 3.0,
            style: Some(TextStyle { content: "Créditos".into(), ..TextStyle::default() }),
            duration: Some(1.0), offset_y: None,
        }).unwrap();
        let cues = caption_cues(editor.project().active(), Some("T1"));
        assert_eq!(cues.len(), 1);
        assert_eq!(cues[0].text, "Subtítulo");
    }

    #[test]
    fn recognition_and_caption_are_one_undoable_project_operation() {
        let mut editor = Editor::new();
        let tx = transcript();
        let commands = vec![
            Command::UpsertTranscript { transcript: tx.clone() },
            Command::AddCaptionClip {
                track_id: Some("T1".into()), above: false, start: 0.2,
                style: Some(TextStyle {
                    content: "Hola mundo".into(), ..TextStyle::default()
                }), duration: Some(1.0), offset_y: None,
                metadata: CaptionMetadata {
                    transcript_id: Some("tx1".into()),
                    segment_id: Some("seg1".into()),
                    ..CaptionMetadata::default()
                },
            },
        ];
        assert!(editor.apply(Command::Batch { commands }).unwrap().applied);
        assert_eq!(editor.project().transcripts(), vec![tx.clone()]);
        let captions = editor.project().caption_clip_ids("TL1");
        assert_eq!(captions.len(), 1);
        let saved = to_document(&settings(), editor.project());
        let loaded = from_document(&saved).expect("can reopen");
        assert_eq!(loaded.transcript("tx1"), Some(tx));
        let caption = &loaded.active().clips[0];
        assert_eq!(caption.caption_metadata().unwrap().transcript_id.as_deref(), Some("tx1"));
        assert_eq!(caption.caption_metadata().unwrap().segment_id.as_deref(), Some("seg1"));
        assert!(editor.undo());
        assert!(editor.project().transcripts().is_empty());
        assert!(editor.project().active().clips.is_empty());
        assert!(editor.redo());
        assert_eq!(editor.project().caption_clip_ids("TL1").len(), 1);
    }

    #[test]
    fn invalid_timing_never_changes_project() {
        let mut editor = Editor::new();
        let mut tx = transcript();
        tx.segments[0].words[0].end = f64::NAN;
        assert!(editor.apply(Command::UpsertTranscript { transcript: tx }).is_err());
        assert!(editor.project().transcripts().is_empty());
    }
}
