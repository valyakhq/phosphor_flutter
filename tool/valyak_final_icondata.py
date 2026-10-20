#!/usr/bin/env python3
"""Make phosphor_flutter compile on Flutter >= 3.44 (valyakhq fork).

Flutter 3.44 made ``IconData`` a ``final`` class whose constructor must be
called with constants (flutter/flutter#181345). Upstream's
``PhosphorIconData extends IconData`` no longer compiles. This script:

1. Rewrites every generated icon constant to a plain ``const IconData(...)``.
2. Keeps ``PhosphorIconData`` / ``PhosphorFlatIconData`` /
   ``PhosphorDuotoneIconData`` as typedefs of ``IconData``, so code that names
   those types keeps compiling.
3. Keeps duotone working: each duotone constant is its primary glyph, and the
   secondary glyph moves to a generated const table that ``PhosphorIcon``
   looks up by code point.
4. Sets ``matchTextDirection`` only on directional glyphs (``mirrors``).
   Upstream mirrored every icon, so a tick, a clock or a QR code came out
   flipped in Arabic.

Idempotent: run it again after merging a new upstream release.
Usage: python3 tool/valyak_final_icondata.py  (from the repo root)
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "lib" / "src"
FLAT_STYLES = ("regular", "thin", "light", "bold", "fill")


def icon_data(code_point: str, style: str) -> str:
    """Unmirrored; ``set_mirroring`` adds the flag to the directional ones."""
    return f"IconData({code_point}, fontFamily: 'Phosphor{style}', fontPackage: 'phosphor_flutter')"


# A glyph mirrors in right-to-left text only when it points along the line:
# back/forward, arrows and carets naming a side, lists and indents (the
# bullets sit at the start), send, sign in/out, toggles, trends. A side that
# is a fixed position rather than a direction (align left, add a column on
# the left, the left mouse button) does not mirror, nor does anything
# symmetric in meaning (check, clock, QR code, scan, refresh).
_SIDE = re.compile(r"(?<=[a-z0-9])(Left|Right)(?=[A-Z0-9]|$)")
_FIXED_SIDE_PREFIXES = ("align", "textAlign", "columnsPlus", "mouse")
_MIRRORED_EXTRAS = frozenset({
    "arrowSquareIn", "arrowSquareOut", "backspace", "keyReturn",
    "paperPlaneRight", "paperPlaneTilt", "phoneIncoming", "phoneOutgoing",
    "sidebar", "sidebarSimple", "signIn", "signOut", "textIndent",
    "textOutdent", "trendDown", "trendUp",
})


def mirrors(name: str) -> bool:
    if name in _MIRRORED_EXTRAS:
        return True
    if name.startswith("list") and name != "list":
        return True
    if name == "arrowsLeftRight" or name.startswith(_FIXED_SIDE_PREFIXES):
        return False
    return bool(_SIDE.search(name))


_CONSTANT = re.compile(
    r"static const (\w+) =(\s+)IconData\((0x[0-9a-f]+), (fontFamily: [^)]*?)(, matchTextDirection: true)?\);"
)
_SECONDARY = re.compile(r"^  (0x[0-9a-f]+): IconData\((.*?)(, matchTextDirection: true)?\),$", re.M)
_FLAG = ", matchTextDirection: true"


def set_mirroring() -> list[str]:
    """Set the flag on every constant from ``mirrors``; returns the mirrored names."""
    mirrored: set[str] = set()
    duotone_mirrored: set[str] = set()
    for style in (*FLAT_STYLES, "duotone"):
        path = SRC / f"phosphor_icons_{style}.dart"

        def replace(m: re.Match[str]) -> str:
            flag = _FLAG if mirrors(m[1]) else ""
            if flag:
                mirrored.add(m[1])
                if style == "duotone":
                    duotone_mirrored.add(m[3])
            return f"static const {m[1]} ={m[2]}IconData({m[3]}, {m[4]}{flag});"

        path.write_text(_CONSTANT.sub(replace, path.read_text()))
    secondaries = SRC / "phosphor_duotone_secondaries.dart"
    secondaries.write_text(
        _SECONDARY.sub(
            lambda m: f"  {m[1]}: IconData({m[2]}{_FLAG if m[1] in duotone_mirrored else ''}),",
            secondaries.read_text(),
        )
    )
    return sorted(mirrored)


UNUSED_IMPORT = "import 'package:phosphor_flutter/src/phosphor_icon_data.dart';\n"


def rewrite_flat(path: Path) -> int:
    text = path.read_text().replace(UNUSED_IMPORT, "")
    pattern = re.compile(r"PhosphorFlatIconData\(\s*(0x[0-9a-fA-F]+),\s*'(\w+)',?\s*\)")
    text, count = pattern.subn(lambda m: icon_data(m.group(1), m.group(2)), text)
    path.write_text(text)
    return count


def rewrite_duotone(path: Path) -> dict[str, str]:
    text = path.read_text()
    pattern = re.compile(
        r"PhosphorDuotoneIconData\(\s*(0x[0-9a-fA-F]+),\s*"
        r"PhosphorIconData\(\s*(0x[0-9a-fA-F]+),\s*'Duotone',?\s*\),?\s*\)"
    )
    secondaries: dict[str, str] = {}

    def replace(m: re.Match[str]) -> str:
        secondaries[m.group(1)] = m.group(2)
        return icon_data(m.group(1), "Duotone")

    text = pattern.sub(replace, text)
    path.write_text(text)
    return secondaries


def write_secondaries(secondaries: dict[str, str]) -> None:
    entries = "\n".join(
        f"  {primary}: {icon_data(secondary, 'Duotone')}," for primary, secondary in secondaries.items()
    )
    (SRC / "phosphor_duotone_secondaries.dart").write_text(
        "// Auto generated by tool/valyak_final_icondata.py\n"
        "// DON'T EDIT BY HAND\n\n"
        "import 'package:flutter/widgets.dart';\n\n"
        "/// Duotone primary code point -> its secondary (background) glyph.\n"
        "const Map<int, IconData> phosphorDuotoneSecondaries = {\n"
        f"{entries}\n"
        "};\n"
    )


ICON_DATA_DART = """library phosphor_flutter;

import 'package:flutter/widgets.dart';
import 'package:phosphor_flutter/src/phosphor_duotone_secondaries.dart';

// valyakhq fork: Flutter >= 3.44 made IconData final (flutter/flutter#181345),
// so these can no longer subclass it. They stay as aliases so code naming the
// types keeps compiling. Regenerate with tool/valyak_final_icondata.py.
typedef PhosphorIconData = IconData;
typedef PhosphorFlatIconData = IconData;
typedef PhosphorDuotoneIconData = IconData;

/// The secondary glyph of a duotone icon, or null for any other icon.
IconData? phosphorDuotoneSecondary(IconData icon) =>
    icon.fontFamily == 'PhosphorDuotone' && icon.fontPackage == 'phosphor_flutter'
        ? phosphorDuotoneSecondaries[icon.codePoint]
        : null;
"""


def rewrite_icon_widget(path: Path) -> None:
    text = path.read_text()
    old = (
        "    if (icon is PhosphorDuotoneIconData) {\n"
        "      final duotoneIcon = icon as PhosphorDuotoneIconData;\n"
    )
    new = (
        "    final secondary = icon == null ? null : phosphorDuotoneSecondary(icon!);\n"
        "    if (secondary != null) {\n"
    )
    if old in text:
        text = text.replace(old, new).replace("duotoneIcon.secondary,", "secondary,")
    path.write_text(text)


def main() -> None:
    for style in FLAT_STYLES:
        count = rewrite_flat(SRC / f"phosphor_icons_{style}.dart")
        print(f"{style}: {count} icons")
    secondaries = rewrite_duotone(SRC / "phosphor_icons_duotone.dart")
    # A few duotone icons (cellSignalNone, wifiNone) have a single layer.
    single = rewrite_flat(SRC / "phosphor_icons_duotone.dart")
    print(f"duotone: {len(secondaries)} two-layer + {single} single-layer icons")
    if secondaries:
        write_secondaries(secondaries)
    (SRC / "phosphor_icon_data.dart").write_text(ICON_DATA_DART)
    rewrite_icon_widget(SRC / "phosphor_icon.dart")
    set_sdk_constraint()
    mirrored = set_mirroring()
    print(f"mirrored in RTL: {len(mirrored)} icons: {' '.join(mirrored)}")


def set_sdk_constraint() -> None:
    """Typedefs of non-function types need Dart >= 2.13; the fork targets 3.x."""
    pubspec = SRC.parent.parent / "pubspec.yaml"
    text = pubspec.read_text()
    text = text.replace('sdk: ">=2.12.0 <4.0.0"', 'sdk: ">=3.0.0 <4.0.0"')
    text = text.replace('flutter: ">=1.17.0"', 'flutter: ">=3.10.0"')
    pubspec.write_text(text)


if __name__ == "__main__":
    main()
