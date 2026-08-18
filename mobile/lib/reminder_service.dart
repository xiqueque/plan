import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest_all.dart' as tzdata;
import 'package:timezone/timezone.dart' as tz;

import 'models.dart';

/// 到点提醒：用安卓系统通知实现（关闭应用后也能到点提醒）。
class ReminderService {
  ReminderService._();

  static final ReminderService instance = ReminderService._();

  final FlutterLocalNotificationsPlugin _plugin =
      FlutterLocalNotificationsPlugin();
  bool _ready = false;

  static const _channelId = 'daily_plan_reminders';
  static const _channelName = '每日计划提醒';

  Future<void> init() async {
    if (_ready) return;
    try {
      tzdata.initializeTimeZones();
      try {
        final name = await FlutterTimezone.getLocalTimezone();
        tz.setLocalLocation(tz.getLocation(name.identifier));
      } catch (_) {
        tz.setLocalLocation(tz.getLocation('Asia/Shanghai'));
      }
      const settings = InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(),
      );
      await _plugin.initialize(settings: settings);
      final android =
          _plugin.resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>();
      await android?.requestNotificationsPermission();
      await android?.requestExactAlarmsPermission();
      _ready = true;
    } catch (_) {
      // 通知不可用时不影响应用使用
    }
  }

  int _idOnce(String taskId) => (taskId.hashCode & 0x7fffffff) % 100000;

  int _idWeekday(String taskId, int weekday) =>
      ((taskId.hashCode & 0x7fffffff) % 900000) + 100000 + weekday;

  /// 按任务设置安排/重排提醒（先取消旧的再排新的，幂等）。
  Future<void> scheduleForTask(Task t) async {
    if (!_ready) return;
    await cancelForTask(t);
    final mode = t.reminderMode;
    final rt = t.reminderTime;
    if (mode == 'none' || rt == null || !rt.contains(':')) return;
    final parts = rt.split(':');
    final hh = int.tryParse(parts[0]) ?? 9;
    final mm = int.tryParse(parts[1]) ?? 0;
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        _channelId,
        _channelName,
        channelDescription: '计划到点提醒',
        importance: Importance.high,
        priority: Priority.high,
      ),
    );
    try {
      if (mode == 'once') {
        final d = DateTime.tryParse(t.date);
        if (d == null) return;
        final when = tz.TZDateTime(tz.local, d.year, d.month, d.day, hh, mm);
        if (!when.isAfter(tz.TZDateTime.now(tz.local))) return;
        await _plugin.zonedSchedule(
          id: _idOnce(t.id),
          title: '每日计划 · 提醒',
          body: t.text,
          scheduledDate: when,
          notificationDetails: details,
          androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        );
      } else {
        final weekdays = t.reminderWeekdays.isEmpty
            ? List.generate(7, (i) => i)
            : t.reminderWeekdays;
        for (final w in weekdays) {
          final next = _nextWeekday(hh, mm, w);
          await _plugin.zonedSchedule(
            id: _idWeekday(t.id, w),
            title: '每日计划 · 提醒',
            body: t.text,
            scheduledDate: next,
            notificationDetails: details,
            androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
            matchDateTimeComponents: DateTimeComponents.dayOfWeekAndTime,
          );
        }
      }
    } catch (_) {
      // 未授予精确闹钟权限时可能失败，不影响使用
    }
  }

  /// 计算下一个「星期 weekday（0=周一…6=周日）」的 hh:mm。
  tz.TZDateTime _nextWeekday(int hh, int mm, int weekday) {
    final now = tz.TZDateTime.now(tz.local);
    var daysAhead = weekday + 1 - now.weekday;
    if (daysAhead < 0) daysAhead += 7;
    if (daysAhead == 0) {
      final todayAt =
          tz.TZDateTime(tz.local, now.year, now.month, now.day, hh, mm);
      if (todayAt.isAfter(now)) return todayAt;
      daysAhead = 7;
    }
    return tz.TZDateTime(
        tz.local, now.year, now.month, now.day + daysAhead, hh, mm);
  }

  Future<void> cancelForTask(Task t) async {
    try {
      await _plugin.cancel(id: _idOnce(t.id));
      for (var w = 0; w < 7; w++) {
        await _plugin.cancel(id: _idWeekday(t.id, w));
      }
    } catch (_) {
      // 忽略取消失败
    }
  }

  /// 应用启动时把所有任务的提醒重排一遍（含重启手机后）。
  Future<void> rescheduleAll(PlanData data) async {
    if (!_ready) return;
    for (final t in data.tasks) {
      await scheduleForTask(t);
    }
  }
}
