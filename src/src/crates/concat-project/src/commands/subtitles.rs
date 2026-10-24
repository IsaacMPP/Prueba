// SPDX-License-Identifier: AGPL-3.0-or-later
//! Project edits for transcription and subtitle identity: one undoable path.
use super::*;

pub(super) fn apply(
    project: &mut Project,
    _mint: &mut IdMint,
    command: Command,
) -> Result<Outcome, CommandError> {
    let applied = match command {
        Command::UpsertTranscript { transcript } => {
            if !transcript.valid() {
                return Err(CommandError::InvalidTranscript);
            }
            project.upsert_transcript(transcript)
        }
        Command::RemoveTranscript { transcript_id } => project.remove_transcript(&transcript_id),
        Command::SetCaptionMetadata { clip_id, metadata } => {
            let Some(clip) = project.active_mut().clip_mut(&clip_id) else {
                return Ok(Outcome::default());
            };
            if clip.kind != ClipKind::Text
                || metadata.as_ref().is_some_and(|meta| !meta.valid_for_clip(clip.duration))
            {
                return Err(CommandError::InvalidCaptionMetadata);
            }
            clip.set_caption_metadata(metadata)
        }
        _ => unreachable!("only subtitle/transcript commands route here"),
    };
    Ok(Outcome { created_id: None, applied })
}
