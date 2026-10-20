import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:phosphor_flutter/phosphor_flutter.dart';

Widget _wrap(Widget child) =>
    Directionality(textDirection: TextDirection.ltr, child: child);

void main() {
  test('icons are plain const IconData in the right font', () {
    const icon = PhosphorIconsRegular.acorn;
    expect(icon.runtimeType, IconData);
    expect(icon.codePoint, 0xeb9a);
    expect(icon.fontFamily, 'PhosphorRegular');
    expect(icon.fontPackage, 'phosphor_flutter');
    expect(icon.matchTextDirection, isFalse);
  });

  test('only directional glyphs mirror in right-to-left text', () {
    for (final style in PhosphorIconsStyle.values) {
      expect(PhosphorIcons.check(style).matchTextDirection, isFalse, reason: '$style');
      expect(PhosphorIcons.clock(style).matchTextDirection, isFalse, reason: '$style');
      expect(PhosphorIcons.qrCode(style).matchTextDirection, isFalse, reason: '$style');
      expect(PhosphorIcons.alignLeft(style).matchTextDirection, isFalse, reason: '$style');
      expect(PhosphorIcons.caretLeft(style).matchTextDirection, isTrue, reason: '$style');
      expect(PhosphorIcons.arrowRight(style).matchTextDirection, isTrue, reason: '$style');
      expect(PhosphorIcons.signOut(style).matchTextDirection, isTrue, reason: '$style');
    }
    // A duotone icon's background layer mirrors with its foreground.
    expect(phosphorDuotoneSecondary(PhosphorIconsDuotone.caretLeft)?.matchTextDirection, isTrue);
    expect(phosphorDuotoneSecondary(PhosphorIconsDuotone.checkCircle)?.matchTextDirection, isFalse);
  });

  test('the style helper returns the matching style constant', () {
    expect(PhosphorIcons.acorn(PhosphorIconsStyle.fill), PhosphorIconsFill.acorn);
  });

  test('only two-layer duotone icons have a secondary glyph', () {
    expect(phosphorDuotoneSecondary(PhosphorIconsDuotone.acorn)?.codePoint, 0xeb9a);
    expect(phosphorDuotoneSecondary(PhosphorIconsDuotone.wifiNone), isNull);
    expect(phosphorDuotoneSecondary(PhosphorIconsRegular.acorn), isNull);
    expect(phosphorDuotoneSecondary(Icons.add), isNull);
  });

  testWidgets('PhosphorIcon stacks both layers for a duotone icon', (tester) async {
    await tester.pumpWidget(_wrap(const PhosphorIcon(PhosphorIconsDuotone.acorn)));
    // The secondary layer is an Icon under an Opacity; the primary is drawn by
    // PhosphorIcon itself (super.build), so it is not an extra Icon widget.
    final secondary = tester.widget<Icon>(find.byType(Icon));
    expect(secondary.icon?.codePoint, 0xeb9a);
    expect(find.byType(Opacity), findsOneWidget);
  });

  testWidgets('PhosphorIcon renders a flat icon once', (tester) async {
    await tester.pumpWidget(_wrap(const PhosphorIcon(PhosphorIconsBold.acorn)));
    expect(find.byType(Opacity), findsNothing);
  });
}
