struct Params {
    cursor: f32,
    word_count: f32,
    mode: f32,
    red: f32,
    green: f32,
    blue: f32,
}

// Every subtitle remains a single editable Text clip. The host supplies
// word timings as a transient keyed value and the title painter supplies
// its per-word reveal map. Both preview and export run this same shader.
//
// Even cursor slots mean a word is active, odd slots mark the silence after
// that word. Fractional interpolation between timed slots never advances
// to the next slot early.
fn effect(uv: vec2<f32>) -> vec4<f32> {
    let c = sample(uv);
    if (params.mode < 0.5 || c.a <= 0.0) {
        return c;
    }

    let slot = floor(params.cursor + 0.00001);
    if (slot < 0.0) {
        return c;
    }
    let word = floor(slot * 0.5);
    let word_is_active = slot - word * 2.0 < 0.5;
    let total = max(1.0, params.word_count);
    // Reveal order is quantised to 8-bit in the title's existing map.
    let ordinal = round(reveal_order(uv) * max(total - 1.0, 0.0));
    var selected = false;
    if (params.mode < 1.5) {
        // Progressively retain each word as it has been spoken.
        selected = ordinal <= word;
    } else {
        // Highlight only the word whose manually editable clock is live.
        selected = word_is_active && abs(ordinal - word) < 0.5;
    }
    if (!selected) {
        return c;
    }
    return vec4<f32>(vec3<f32>(params.red, params.green, params.blue), c.a);
}
