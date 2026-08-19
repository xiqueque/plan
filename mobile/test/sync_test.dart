import 'package:flutter_test/flutter_test.dart';

import 'package:daily_plan/models.dart';
import 'package:daily_plan/sync_page.dart';

void main() {
  test('applyRemoteData 保留手机本地设置', () {
    final local = PlanData();
    local.settings['theme'] = '碧海晴空';
    local.settings['sound'] = false;
    local.settings['sync_ip'] = '192.168.1.5';
    final remote = <String, dynamic>{
      'settings': {'cleanup_days': 7},
      'tasks': [
        {
          'id': 'abc',
          'text': '来自电脑',
          'date': '2026-08-19',
          'time_start': null,
          'time_end': null,
          'is_daily': false,
          'color': '#1F3A4D',
          'reminder_mode': 'none',
          'reminder_time': null,
          'reminder_weekdays': [0, 1, 2, 3, 4, 5, 6],
          'images': [],
          'pinned': false,
          'pinned_at': null,
          'created_at': 1,
        }
      ],
      'timetable': [],
      'done': {},
      'reminded': {},
      'day_images': {},
      'image_names': {},
      'image_daily': {},
      'notes': '电脑便签',
    };
    applyRemoteData(local, remote);
    expect(local.settings['theme'], '碧海晴空');
    expect(local.settings['sound'], false);
    expect(local.settings['sync_ip'], '192.168.1.5');
    expect(local.settings['cleanup_days'], 7);
    expect(local.tasks.single.text, '来自电脑');
    expect(local.notes, '电脑便签');
  });
}
