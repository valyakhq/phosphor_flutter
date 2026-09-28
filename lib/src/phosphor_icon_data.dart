library phosphor_flutter;

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
