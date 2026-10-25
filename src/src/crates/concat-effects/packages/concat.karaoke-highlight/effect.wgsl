struct Params {
    cursor: f32,
    word_count: f32,
    mode: f32,
    red: f32,
    green: f32,
    blue: f32,
    word_x: f32,
    word_y: f32,
    word_half_w: f32,
    word_half_h: f32,
}

// Every subtitle remains a single editable Text clip. The host supplies
// word timings as a transient keyed value and the title painter supplies
// its per-word reveal map. Both preview and export run this same shader.
//
// Even cursor slots mean a word is active, odd slots mark the silence after
// that word. Fractional interpolation between timed slots never advances
// to the next slot early.
fn effect(uv: vec2<f32>) -> vec4<f32> {
    if (params.mode < 0.5) {
        return sample(uv);
    }

    let slot = floor(params.cursor + 0.00001);
    let word = floor(slot * 0.5);
    let word_is_active = slot - word * 2.0 < 0.5;
    let total = max(1.0, params.word_count);

    // Premiere-like Single Word: the original project keeps a single
    // editable subtitle, but this GPU pass crops its selected word and
    // places it at the frame centre. No extra title clips are generated.
    if (params.mode >= 1.5) {
        if (slot < 0.0 || !word_is_active) {
            return vec4<f32>(0.0);
        }
        let position = vec2<f32>(params.word_x, params.word_y);
        let source_uv = uv + position - vec2<f32>(0.5);
        if (abs(source_uv.x - position.x) > params.word_half_w
            || abs(source_uv.y - position.y) > params.word_half_h) {
            return vec4<f32>(0.0);
        }
        let px = sample(source_uv);
        if (px.a <= 0.0) {
            return px;
        }
        let ordinal = round(reveal_order(source_uv) * max(total - 1.0, 0.0));
        if (abs(ordinal - word) > 0.5) {
            return vec4<f32>(0.0);
        }
        return vec4<f32>(vec3<f32>(params.red, params.green, params.blue), px.a);
    }

    // Progressive mode keeps the original phrase in place and colours
    // each word as it is spoken. The Normal mode bypasses this shader.
    let px = sample(uv);
    if (px.a <= 0.0 || slot < 0.0) {
        return px;
    }
    let ordinal = round(reveal_order(uv) * max(total - 1.0, 0.0));
    if (ordinal > word) {
        return px;
    }
    return vec4<f32>(vec3<f32>(params.red, params.green, params.blue), px.a);
}
