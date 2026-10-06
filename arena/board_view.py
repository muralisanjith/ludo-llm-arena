from arena.board import RED, GREEN, YELLOW, BLUE, OFFSETS, SAFE_SQUARES, display_token

TRACK_COORDS = [
    (1, 6), (2, 6), (3, 6), (4, 6), (5, 6), (6, 5), (6, 4), (6, 3), (6, 2), (6, 1), (6, 0), (7, 0),
    (8, 0), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (9, 6), (10, 6), (11, 6), (12, 6), (13, 6), (14, 6),
    (14, 7), (14, 8), (13, 8), (12, 8), (11, 8), (10, 8), (9, 8), (8, 9), (8, 10), (8, 11), (8, 12), (8, 13),
    (8, 14), (7, 14), (6, 14), (6, 13), (6, 12), (6, 11), (6, 10), (6, 9), (5, 8), (4, 8), (3, 8), (2, 8),
    (1, 8), (0, 8), (0, 7), (0, 6)
]

HOME_STRETCH_COORDS = {
    RED: [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7)],
    GREEN: [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5)],
    YELLOW: [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7)],
    BLUE: [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9)]
}

FINISHED_COORDS = {
    RED: (6, 7),
    GREEN: (7, 6),
    YELLOW: (8, 7),
    BLUE: (7, 8)
}

BASE_YARD_COORDS = {
    RED: [(1.5, 1.5), (3.5, 1.5), (1.5, 3.5), (3.5, 3.5)],
    GREEN: [(10.5, 1.5), (12.5, 1.5), (10.5, 3.5), (12.5, 3.5)],
    YELLOW: [(10.5, 10.5), (12.5, 10.5), (10.5, 12.5), (12.5, 12.5)],
    BLUE: [(1.5, 10.5), (3.5, 10.5), (1.5, 12.5), (3.5, 12.5)]
}

COLOR_HEX = {
    RED: "#EF4444",
    GREEN: "#10B981",
    YELLOW: "#F59E0B",
    BLUE: "#3B82F6"
}

LIGHT_HEX = {
    RED: "#FEE2E2",
    GREEN: "#D1FAE5",
    YELLOW: "#FEF3C7",
    BLUE: "#DBEAFE"
}

DARK_HEX = {
    RED: "#991B1B",
    GREEN: "#065F46",
    YELLOW: "#92400E",
    BLUE: "#1E40AF"
}

TOKEN_TEXT_COLOR = {
    RED: "#FFFFFF",
    GREEN: "#FFFFFF",
    YELLOW: "#1F2937",
    BLUE: "#FFFFFF"
}

BASE_TOKEN_TEXT_COLOR = {
    RED: DARK_HEX[RED],       # #991B1B - deep crimson on pastel red
    GREEN: DARK_HEX[GREEN],   # #065F46 - deep emerald on pastel green
    YELLOW: DARK_HEX[YELLOW], # #92400E - deep amber on pastel yellow
    BLUE: DARK_HEX[BLUE]      # #1E40AF - deep navy on pastel blue
}


def get_token_center(color, token_id, prog):
    if prog == -1:
        gx, gy = BASE_YARD_COORDS[color][token_id]
        return gx * 40 + 20, gy * 40 + 20
    elif prog == 56:
        gx, gy = FINISHED_COORDS[color]
        return gx * 40 + 20, gy * 40 + 20
    elif prog >= 51:
        idx = prog - 51
        gx, gy = HOME_STRETCH_COORDS[color][idx]
        return gx * 40 + 20, gy * 40 + 20
    else:
        abs_sq = (OFFSETS[color] + prog) % 52
        gx, gy = TRACK_COORDS[abs_sq]
        return gx * 40 + 20, gy * 40 + 20


BASE_BOX_CENTERS = {
    RED: (120, 120),
    GREEN: (480, 120),
    YELLOW: (480, 480),
    BLUE: (120, 480)
}


def to_svg(board) -> str:
    cs = 40  # cell size
    board_size = 600

    svg_parts = []
    svg_parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {board_size} {board_size}" width="100%" height="100%">')
    svg_parts.append('''<defs>
        <style>
            @keyframes dropPiece {
                0% { transform: scale(1.8); opacity: 0.5; stroke-width: 5px; }
                50% { transform: scale(1.3); opacity: 1; stroke-width: 4px; }
                100% { transform: scale(1.0); opacity: 1; stroke-width: 2px; }
            }
            @keyframes diceDropRed {
                0% { transform: translateY(-160px) rotate(-180deg) scale(1.6); opacity: 0; }
                70% { transform: translateY(10px) rotate(10deg) scale(1.1); opacity: 1; }
                100% { transform: translateY(0px) rotate(0deg) scale(1.0); opacity: 1; }
            }
            @keyframes diceDropGreen {
                0% { transform: translateY(-160px) rotate(180deg) scale(1.6); opacity: 0; }
                70% { transform: translateY(10px) rotate(-10deg) scale(1.1); opacity: 1; }
                100% { transform: translateY(0px) rotate(0deg) scale(1.0); opacity: 1; }
            }
            @keyframes diceDropYellow {
                0% { transform: translateY(-160px) rotate(-180deg) scale(1.6); opacity: 0; }
                70% { transform: translateY(10px) rotate(10deg) scale(1.1); opacity: 1; }
                100% { transform: translateY(0px) rotate(0deg) scale(1.0); opacity: 1; }
            }
            @keyframes diceDropBlue {
                0% { transform: translateY(-160px) rotate(180deg) scale(1.6); opacity: 0; }
                70% { transform: translateY(10px) rotate(-10deg) scale(1.1); opacity: 1; }
                100% { transform: translateY(0px) rotate(0deg) scale(1.0); opacity: 1; }
            }
            .dice-drop-red { animation: diceDropRed 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; transform-origin: 120px 120px; }
            .dice-drop-green { animation: diceDropGreen 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; transform-origin: 480px 120px; }
            .dice-drop-yellow { animation: diceDropYellow 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; transform-origin: 480px 480px; }
            .dice-drop-blue { animation: diceDropBlue 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; transform-origin: 120px 480px; }
            .new-piece {
                animation: dropPiece 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
                transform-box: fill-box;
                transform-origin: center;
            }
            .token { transition: all 0.3s ease; }
            .token:hover { cursor: pointer; filter: brightness(1.15); }
        </style>
        <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.3"/>
        </filter>
    </defs>''')

    # Background
    svg_parts.append(f'<rect width="{board_size}" height="{board_size}" fill="#F9FAFB"/>')

    # Base Squares (6x6 cells each)
    bases = [
        (0, 0, RED),
        (9, 0, GREEN),
        (9, 9, YELLOW),
        (0, 9, BLUE)
    ]
    for bx, by, color in bases:
        svg_parts.append(f'<rect x="{bx*cs}" y="{by*cs}" width="{6*cs}" height="{6*cs}" fill="{COLOR_HEX[color]}"/>')
        # Inner white yard
        svg_parts.append(f'<rect x="{(bx+1)*cs}" y="{(by+1)*cs}" width="{4*cs}" height="{4*cs}" rx="12" fill="#FFFFFF" filter="url(#shadow)"/>')

    # Per-Player Dice Box inside active player's base
    curr_c = getattr(board, 'dice_player', None) or board.current_player
    if board.dice is not None and curr_c in BASE_BOX_CENTERS:
        dcx, dcy = BASE_BOX_CENTERS[curr_c]
        dice_val = board.dice
        anim_class = f"dice-drop-{curr_c.lower()}"

        box_size = 46
        bx = dcx - box_size / 2
        by = dcy - box_size / 2
        roll_id = getattr(board, "roll_count", 0)
        svg_parts.append(
            f'<g class="{anim_class}" id="dice-roll-{roll_id}">'
            f'<rect x="{bx}" y="{by}" width="{box_size}" height="{box_size}" rx="10" '
            f'fill="#FFFFFF" stroke="{COLOR_HEX[curr_c]}" stroke-width="3" filter="url(#shadow)"/>'
        )

        pip_r = 4.5
        dot_fill = DARK_HEX[curr_c]
        d_off = 10.5

        pips = []
        if dice_val in (1, 3, 5):
            pips.append((0, 0))
        if dice_val in (2, 3, 4, 5, 6):
            pips.append((-d_off, -d_off))
            pips.append((d_off, d_off))
        if dice_val in (4, 5, 6):
            pips.append((d_off, -d_off))
            pips.append((-d_off, d_off))
        if dice_val == 6:
            pips.append((-d_off, 0))
            pips.append((d_off, 0))

        for px, py in pips:
            svg_parts.append(f'<circle cx="{dcx + px}" cy="{dcy + py}" r="{pip_r}" fill="{dot_fill}"/>')

        svg_parts.append('</g>')

    # Outer Track Squares Grid Lines & Fill
    for abs_sq, (gx, gy) in enumerate(TRACK_COORDS):
        bg = "#FFFFFF"
        if abs_sq == 0:
            bg = LIGHT_HEX[RED]
        elif abs_sq == 13:
            bg = LIGHT_HEX[GREEN]
        elif abs_sq == 26:
            bg = LIGHT_HEX[YELLOW]
        elif abs_sq == 39:
            bg = LIGHT_HEX[BLUE]
        elif abs_sq in SAFE_SQUARES:
            bg = "#F3F4F6"

        svg_parts.append(f'<rect x="{gx*cs}" y="{gy*cs}" width="{cs}" height="{cs}" fill="{bg}" stroke="#E5E7EB" stroke-width="1"/>')

        # Draw Star icon on safe star squares
        if abs_sq in {8, 21, 34, 47}:
            cx, cy = gx * cs + cs / 2, gy * cs + cs / 2
            svg_parts.append(f'<text x="{cx}" y="{cy+5}" font-size="18" text-anchor="middle" fill="#9CA3AF">&#9733;</text>')

    # Home Stretches
    for color, coords in HOME_STRETCH_COORDS.items():
        for gx, gy in coords:
            svg_parts.append(f'<rect x="{gx*cs}" y="{gy*cs}" width="{cs}" height="{cs}" fill="{COLOR_HEX[color]}" opacity="0.85" stroke="#FFFFFF" stroke-width="1"/>')

    # Center Home Triangles (3x3 area at cell 6..8, 6..8)
    # Triangles meeting at center (7.5*cs, 7.5*cs)
    center_x, center_y = 7.5 * cs, 7.5 * cs
    svg_parts.append(f'<polygon points="{6*cs},{6*cs} {6*cs},{9*cs} {center_x},{center_y}" fill="{COLOR_HEX[RED]}"/>')
    svg_parts.append(f'<polygon points="{6*cs},{6*cs} {9*cs},{6*cs} {center_x},{center_y}" fill="{COLOR_HEX[GREEN]}"/>')
    svg_parts.append(f'<polygon points="{9*cs},{6*cs} {9*cs},{9*cs} {center_x},{center_y}" fill="{COLOR_HEX[YELLOW]}"/>')
    svg_parts.append(f'<polygon points="{6*cs},{9*cs} {9*cs},{9*cs} {center_x},{center_y}" fill="{COLOR_HEX[BLUE]}"/>')
    svg_parts.append(f'<rect x="{6*cs}" y="{6*cs}" width="{3*cs}" height="{3*cs}" fill="none" stroke="#D1D5DB" stroke-width="2"/>')

    # Group tokens by coordinate to offset stacked tokens
    coord_tokens = {}
    for color in [RED, GREEN, YELLOW, BLUE]:
        for t_id, prog in enumerate(board.tokens[color]):
            cx, cy = get_token_center(color, t_id, prog)
            pos_key = (cx, cy)
            if pos_key not in coord_tokens:
                coord_tokens[pos_key] = []
            coord_tokens[pos_key].append((color, t_id, prog))

    # Render Tokens (Single circle per token)
    for (cx, cy), tokens_at_pos in coord_tokens.items():
        n = len(tokens_at_pos)
        for i, (color, t_id, prog) in enumerate(tokens_at_pos):
            # Apply slight offset if stacked on track / finish
            if n > 1 and prog != -1:
                dx = (i - (n - 1) / 2) * 6
                dy = (i - (n - 1) / 2) * 6
            else:
                dx, dy = 0, 0

            tcx, tcy = cx + dx, cy + dy
            is_new = (color == board.latest_color and t_id == board.latest_token)
            anim_class = " new-piece" if is_new else ""

            if prog == -1:
                # STATE A - Token in base:
                # Single circle, light pastel fill, colored stroke, centered darker-tinted number text
                svg_parts.append(
                    f'<circle class="token" cx="{tcx}" cy="{tcy}" r="14" '
                    f'fill="{LIGHT_HEX[color]}" stroke="{COLOR_HEX[color]}" stroke-width="2.5"/>'
                )
                svg_parts.append(
                    f'<text x="{tcx}" y="{tcy}" font-size="11" font-weight="bold" font-family="sans-serif" '
                    f'text-anchor="middle" dominant-baseline="central" fill="{BASE_TOKEN_TEXT_COLOR[color]}" '
                    f'pointer-events="none">{display_token(t_id)}</text>'
                )
            else:
                # STATE B - Token on track, in home column, or finished (progress >= 0):
                # Solid fill in player color with white border and shadow
                svg_parts.append(
                    f'<circle class="token{anim_class}" cx="{tcx}" cy="{tcy}" r="14" '
                    f'fill="{COLOR_HEX[color]}" stroke="#FFFFFF" stroke-width="2.5" filter="url(#shadow)"/>'
                )
                # Centered number text directly inside the same circle
                svg_parts.append(
                    f'<text x="{tcx}" y="{tcy}" font-size="11" font-weight="bold" font-family="sans-serif" '
                    f'text-anchor="middle" dominant-baseline="central" fill="{TOKEN_TEXT_COLOR[color]}" '
                    f'pointer-events="none">{display_token(t_id)}</text>'
                )

    svg_parts.append('</svg></div>')
    return '<div style="max-width: 640px; margin: 0 auto; width: 100%; display: flex; justify-content: center;">' + "".join(svg_parts)
