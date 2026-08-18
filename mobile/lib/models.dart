import 'dart:math';

import 'package:flutter/material.dart';

/// 颜色选项：与电脑版一致（默认深蓝灰 / 红 / 橙 / 蓝 / 绿 / 紫）
const List<(String, String)> taskColors = [
  ('#1F3A4D', '默认'),
  ('#E53935', '红'),
  ('#FB8C00', '橙'),
  ('#1E88E5', '蓝'),
  ('#43A047', '绿'),
  ('#8E24AA', '紫'),
];

Color colorFromHex(String hex) {
  final h = hex.replaceFirst('#', '');
  return Color(int.parse('FF$h', radix: 16));
}

String newTaskId() {
  final r = Random();
  final s = DateTime.now().microsecondsSinceEpoch.toRadixString(16) +
      List.generate(8, (_) => r.nextInt(16).toRadixString(16)).join();
  return s.substring(s.length - 12);
}

class Task {
  String id;
  String text;
  String date; // YYYY-MM-DD
  String? timeStart;
  String? timeEnd;
  bool isDaily;
  String color;
  String reminderMode;
  String? reminderTime;
  List<int> reminderWeekdays;
  List<String> images;
  bool pinned;
  double? pinnedAt;
  double createdAt;

  Task({
    required this.id,
    required this.text,
    required this.date,
    this.timeStart,
    this.timeEnd,
    this.isDaily = false,
    this.color = '#1F3A4D',
    this.reminderMode = 'none',
    this.reminderTime,
    List<int>? reminderWeekdays,
    List<String>? images,
    this.pinned = false,
    this.pinnedAt,
    required this.createdAt,
  })  : reminderWeekdays = reminderWeekdays ?? List.generate(7, (i) => i),
        images = images ?? [];

  factory Task.fromJson(Map<String, dynamic> j) {
    return Task(
      id: (j['id'] ?? '').toString(),
      text: (j['text'] ?? '').toString(),
      date: (j['date'] ?? '').toString(),
      timeStart: j['time_start']?.toString(),
      timeEnd: j['time_end']?.toString(),
      isDaily: j['is_daily'] == true,
      color: (j['color'] ?? '#1F3A4D').toString(),
      reminderMode: (j['reminder_mode'] ?? 'none').toString(),
      reminderTime: j['reminder_time']?.toString(),
      reminderWeekdays: (j['reminder_weekdays'] as List?)
          ?.map((e) => (e as num).toInt())
          .toList(),
      images: (j['images'] as List?)?.map((e) => e.toString()).toList(),
      pinned: j['pinned'] == true,
      pinnedAt: (j['pinned_at'] as num?)?.toDouble(),
      createdAt: (j['created_at'] as num?)?.toDouble() ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'text': text,
        'date': date,
        'time_start': timeStart,
        'time_end': timeEnd,
        'is_daily': isDaily,
        'color': color,
        'reminder_mode': reminderMode,
        'reminder_time': reminderTime,
        'reminder_weekdays': reminderWeekdays,
        'images': images,
        'pinned': pinned,
        'pinned_at': pinnedAt,
        'created_at': createdAt,
      };

  Task copyWith({
    String? text,
    String? date,
    String? timeStart,
    String? timeEnd,
    bool? isDaily,
    String? color,
    String? reminderMode,
    String? reminderTime,
    List<int>? reminderWeekdays,
    bool? pinned,
    double? pinnedAt,
  }) {
    return Task(
      id: id,
      text: text ?? this.text,
      date: date ?? this.date,
      timeStart: timeStart ?? this.timeStart,
      timeEnd: timeEnd ?? this.timeEnd,
      isDaily: isDaily ?? this.isDaily,
      color: color ?? this.color,
      reminderMode: reminderMode ?? this.reminderMode,
      reminderTime: reminderTime ?? this.reminderTime,
      reminderWeekdays: reminderWeekdays ?? this.reminderWeekdays,
      images: images,
      pinned: pinned ?? this.pinned,
      pinnedAt: pinnedAt ?? this.pinnedAt,
      createdAt: createdAt,
    );
  }
}

class PlanData {
  Map<String, dynamic> settings;
  List<Task> tasks;
  List<Course> timetable;
  Map<String, Map<String, bool>> done; // date -> {taskId: true}
  Map<String, Map<String, String>> reminded;
  Map<String, List<String>> dayImages;
  Map<String, String> imageNames;
  Map<String, bool> imageDaily;
  String notes;

  PlanData({
    Map<String, dynamic>? settings,
    List<Task>? tasks,
    List<Course>? timetable,
    Map<String, Map<String, bool>>? done,
    Map<String, Map<String, String>>? reminded,
    Map<String, List<String>>? dayImages,
    Map<String, String>? imageNames,
    Map<String, bool>? imageDaily,
    String? notes,
  })  : settings = settings ?? {'cleanup_days': 0, 'sound_volume': 12},
        tasks = tasks ?? [],
        timetable = timetable ?? [],
        done = done ?? {},
        reminded = reminded ?? {},
        dayImages = dayImages ?? {},
        imageNames = imageNames ?? {},
        imageDaily = imageDaily ?? {},
        notes = notes ?? '';

  factory PlanData.fromJson(Map<String, dynamic> j) {
    return PlanData(
      settings: Map<String, dynamic>.from((j['settings'] as Map?) ?? {}),
      tasks: (j['tasks'] as List?)
              ?.map((e) => Task.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      timetable: (j['timetable'] as List?)
              ?.map((e) => Course.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      done: _doneFromJson(j['done']),
      reminded: _remindedFromJson(j['reminded']),
      dayImages: _dayImagesFromJson(j['day_images']),
      imageNames:
          Map<String, String>.from((j['image_names'] as Map?) ?? {}),
      imageDaily: Map<String, bool>.from((j['image_daily'] as Map?) ?? {}),
      notes: (j['notes'] ?? '').toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'settings': settings,
        'tasks': tasks.map((t) => t.toJson()).toList(),
        'timetable': timetable.map((c) => c.toJson()).toList(),
        'done': done,
        'reminded': reminded,
        'day_images': dayImages,
        'image_names': imageNames,
        'image_daily': imageDaily,
        'notes': notes,
      };

  /// 某天要显示的任务（每天重复任务 + 当天任务），已排序。
  List<Task> tasksForDate(String dateStr) {
    final list = tasks.where((t) => t.isDaily || t.date == dateStr).toList();
    list.sort(taskSort);
    return list;
  }

  bool isDone(String taskId, String dateStr) => done[dateStr]?[taskId] == true;

  void setDone(String taskId, String dateStr, bool value) {
    if (value) {
      (done[dateStr] ??= {})[taskId] = true;
    } else {
      done[dateStr]?.remove(taskId);
    }
  }
}

/// 一周课程表里的一门课。
class Course {
  String id;
  int weekday; // 0=周一 … 6=周日
  String name;
  String? timeStart; // HH:mm，可空
  String? timeEnd; // HH:mm，可空
  String color;
  String room;

  Course({
    required this.id,
    required this.weekday,
    required this.name,
    this.timeStart,
    this.timeEnd,
    this.color = '#1F3A4D',
    this.room = '',
  });

  factory Course.fromJson(Map<String, dynamic> j) {
    return Course(
      id: (j['id'] ?? '').toString(),
      weekday: (j['weekday'] as num?)?.toInt() ?? 0,
      name: (j['name'] ?? '').toString(),
      timeStart: j['time_start']?.toString(),
      timeEnd: j['time_end']?.toString(),
      color: (j['color'] ?? '#1F3A4D').toString(),
      room: (j['room'] ?? '').toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'weekday': weekday,
        'name': name,
        'time_start': timeStart,
        'time_end': timeEnd,
        'color': color,
        'room': room,
      };
}

/// 排序：置顶优先（按置顶时间），其余按时段、创建时间。
int taskSort(Task a, Task b) {
  if (a.pinned != b.pinned) return a.pinned ? -1 : 1;
  if (a.pinned && b.pinned) {
    return (a.pinnedAt ?? 0).compareTo(b.pinnedAt ?? 0);
  }
  final ta = a.timeStart ?? '';
  final tb = b.timeStart ?? '';
  if (ta != tb) return ta.compareTo(tb);
  return a.createdAt.compareTo(b.createdAt);
}

/// 时间段显示：结束早于开始时视为跨午夜，标为「次日」。
String formatTimePeriod(String? start, String? end) {
  if (start == null || start.isEmpty) return '';
  if (end == null || end.isEmpty) return start;
  if (end.compareTo(start) < 0) return '$start – 次日$end';
  return '$start – $end';
}

Map<String, Map<String, bool>> _doneFromJson(dynamic j) {
  final result = <String, Map<String, bool>>{};
  if (j is Map) {
    j.forEach((k, v) {
      final m = <String, bool>{};
      if (v is Map) {
        v.forEach((id, val) => m[id.toString()] = val == true);
      }
      result[k.toString()] = m;
    });
  }
  return result;
}

Map<String, Map<String, String>> _remindedFromJson(dynamic j) {
  final result = <String, Map<String, String>>{};
  if (j is Map) {
    j.forEach((k, v) {
      final m = <String, String>{};
      if (v is Map) {
        v.forEach((id, val) => m[id.toString()] = val.toString());
      }
      result[k.toString()] = m;
    });
  }
  return result;
}

Map<String, List<String>> _dayImagesFromJson(dynamic j) {
  final result = <String, List<String>>{};
  if (j is Map) {
    j.forEach((k, v) {
      result[k.toString()] =
          (v as List?)?.map((e) => e.toString()).toList() ?? [];
    });
  }
  return result;
}
