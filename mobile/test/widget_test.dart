import 'package:flutter_test/flutter_test.dart';

import 'package:daily_plan/main.dart';

void main() {
  testWidgets('App renders main screen', (WidgetTester tester) async {
    await tester.pumpWidget(const DailyPlanApp());
    await tester.pumpAndSettle();
    expect(find.textContaining('计划'), findsWidgets);
  });
}
