import 'package:flutter/material.dart';

import 'fx.dart';
import 'models.dart';
import 'theme.dart';

/// 课表：网格视图（时间列 + 周一~周日 7 列），可增删改。
class TimetablePage extends StatefulWidget {
  final PlanData data;
  final VoidCallback onChanged;

  const TimetablePage({super.key, required this.data, required this.onChanged});

  @override
  State<TimetablePage> createState() => _TimetablePageState();
}

class _TimetablePageState extends State<TimetablePage> {
  static const _dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  static const _colWidth = 66.0;
  static const _timeColWidth = 58.0;

  List<(String, String)> get _timeRanges {
    final ranges = <(String, String)>[];
    final list = widget.data.timetable.toList()
      ..sort((a, b) => a.timeStart.compareTo(b.timeStart));
    for (final c in list) {
      if (!ranges.any((r) => r.$1 == c.timeStart && r.$2 == c.timeEnd)) {
        ranges.add((c.timeStart, c.timeEnd));
      }
    }
    return ranges;
  }

  List<Course> _coursesAt((String, String) range, int weekday) {
    return widget.data.timetable
        .where((c) =>
            c.weekday == weekday &&
            c.timeStart == range.$1 &&
            c.timeEnd == range.$2)
        .toList();
  }

  Future<void> _openCourseDialog({
    Course? course,
    int? initialWeekday,
    String? initialStart,
    String? initialEnd,
  }) async {
    final result = await showDialog<Object>(
      context: context,
      builder: (_) => CourseDialog(
        course: course,
        initialWeekday: initialWeekday,
        initialStart: initialStart,
        initialEnd: initialEnd,
      ),
    );
    if (result == null) return;
    if (result == 'delete' && course != null) {
      await _deleteCourse(course);
      return;
    }
    if (result is! Course) return;
    setState(() {
      if (course == null) {
        widget.data.timetable.add(result);
      } else {
        final idx = widget.data.timetable.indexWhere((c) => c.id == course.id);
        if (idx >= 0) {
          widget.data.timetable[idx] = result;
        }
      }
    });
    widget.onChanged();
  }

  Future<void> _deleteCourse(Course c) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除课程'),
        content: Text('确定删除「${c.name}」吗？'),
        actions: [
          TextButton(
            onPressed: () {
              Fx.tap();
              Navigator.pop(ctx, false);
            },
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () {
              Fx.tap();
              Navigator.pop(ctx, true);
            },
            child: const Text('删除'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    setState(() {
      widget.data.timetable.removeWhere((x) => x.id == c.id);
    });
    widget.onChanged();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: T.t.bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('课表',
            style: TextStyle(fontWeight: FontWeight.bold, color: T.t.text)),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: T.t.text),
          onPressed: () {
            Fx.tap();
            Navigator.pop(context);
          },
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.add_circle_outline, color: T.t.primary),
            onPressed: () => _openCourseDialog(),
          ),
        ],
      ),
      body: widget.data.timetable.isEmpty ? _buildEmpty() : _buildGrid(),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('🗓️', style: TextStyle(fontSize: 56)),
          const SizedBox(height: 12),
          Text('还没有课程~\n点右上角 ＋ 添加，或点网格空白处直接加',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 14, color: T.t.hint, height: 1.6)),
        ],
      ),
    );
  }

  Widget _buildGrid() {
    final now = DateTime.now();
    final todayIdx = now.weekday - 1;
    final ranges = _timeRanges;
    final totalWidth = _timeColWidth + 7 * _colWidth;

    return LayoutBuilder(
      builder: (ctx, cons) => SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: SizedBox(
          width: totalWidth,
          height: cons.maxHeight,
          child: SingleChildScrollView(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDayHeader(todayIdx),
                const SizedBox(height: 4),
                ...ranges.map((r) => _buildTimeRow(r, todayIdx)),
                const SizedBox(height: 12),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildDayHeader(int todayIdx) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(width: _timeColWidth),
        ...List.generate(7, (d) {
          final isToday = d == todayIdx;
          return Container(
            width: _colWidth,
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Center(
              child: Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                decoration: BoxDecoration(
                  color: isToday ? T.t.primary : Colors.transparent,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _dayNames[d],
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: isToday ? Colors.white : T.t.hint,
                  ),
                ),
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildTimeRow((String, String) range, int todayIdx) {
    final cells = List.generate(7, (d) => _coursesAt(range, d));
    final maxCount = cells.fold(1, (m, l) => l.length > m ? l.length : m);
    final rowH = 56 + (maxCount - 1) * 40.0;
    final cardH = maxCount == 1
        ? rowH - 14
        : (rowH - 10 - (maxCount - 1) * 6) / maxCount;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: T.t.card,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            width: _timeColWidth - 4,
            padding: const EdgeInsets.symmetric(horizontal: 4),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  range.$1,
                  style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: T.t.text),
                ),
                Text(
                  range.$2,
                  style: TextStyle(fontSize: 10, color: T.t.hint),
                ),
              ],
            ),
          ),
          ...List.generate(7, (d) {
            final list = cells[d];
            return Container(
              width: _colWidth,
              height: rowH,
              padding: const EdgeInsets.all(3),
              child: list.isEmpty
                  ? InkWell(
                      onTap: () => _openCourseDialog(
                        initialWeekday: d,
                        initialStart: range.$1,
                        initialEnd: range.$2,
                      ),
                      borderRadius: BorderRadius.circular(9),
                      child: Container(
                        decoration: BoxDecoration(
                          color: T.t.bg,
                          borderRadius: BorderRadius.circular(9),
                        ),
                      ),
                    )
                  : Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        for (final c in list) _buildMiniCard(c, cardH),
                      ],
                    ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildMiniCard(Course c, double height) {
    final color = colorFromHex(c.color);
    return GestureDetector(
      onTap: () => _openCourseDialog(course: c),
      onLongPress: () => _deleteCourse(c),
      child: Container(
        height: height,
        width: double.infinity,
        margin: const EdgeInsets.symmetric(vertical: 2),
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.16),
          borderRadius: BorderRadius.circular(9),
          border: Border.all(color: color.withValues(alpha: 0.45), width: 1),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              c.name,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: color,
                height: 1.2,
              ),
            ),
            if (c.room.isNotEmpty && height > 30)
              Text(
                c.room,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 8, color: T.t.hint),
              ),
          ],
        ),
      ),
    );
  }
}

class CourseDialog extends StatefulWidget {
  final Course? course;
  final int? initialWeekday;
  final String? initialStart;
  final String? initialEnd;

  const CourseDialog({
    super.key,
    this.course,
    this.initialWeekday,
    this.initialStart,
    this.initialEnd,
  });

  @override
  State<CourseDialog> createState() => _CourseDialogState();
}

class _CourseDialogState extends State<CourseDialog> {
  static const _dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  late final TextEditingController _nameCtrl;
  late final TextEditingController _roomCtrl;
  late int _weekday;
  late String _color;
  TimeOfDay? _start;
  TimeOfDay? _end;

  @override
  void initState() {
    super.initState();
    final c = widget.course;
    _nameCtrl = TextEditingController(text: c?.name ?? '');
    _roomCtrl = TextEditingController(text: c?.room ?? '');
    _weekday = c?.weekday ?? widget.initialWeekday ?? 0;
    _color = c?.color ?? '#1F3A4D';
    _start = _parse(c?.timeStart) ?? _parse(widget.initialStart);
    _end = _parse(c?.timeEnd) ?? _parse(widget.initialEnd);
  }

  TimeOfDay? _parse(String? s) {
    if (s == null || !s.contains(':')) return null;
    final p = s.split(':');
    return TimeOfDay(hour: int.parse(p[0]), minute: int.parse(p[1]));
  }

  String _fmt(TimeOfDay? t) => t == null
      ? ''
      : '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  Future<void> _pick(bool isStart) async {
    Fx.tap();
    final picked = await showTimePicker(
      context: context,
      initialTime: isStart
          ? (_start ?? const TimeOfDay(hour: 8, minute: 0))
          : (_end ?? const TimeOfDay(hour: 9, minute: 50)),
    );
    if (picked == null) return;
    setState(() {
      if (isStart) {
        _start = picked;
      } else {
        _end = picked;
      }
    });
  }

  void _save() {
    final name = _nameCtrl.text.trim();
    if (name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('写个课程名吧~')),
      );
      return;
    }
    final start = _fmt(_start);
    final end = _fmt(_end);
    if (start.isEmpty || end.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请选择开始和结束时间')),
      );
      return;
    }
    final old = widget.course;
    Navigator.pop(
      context,
      Course(
        id: old?.id ?? newTaskId(),
        weekday: _weekday,
        name: name,
        timeStart: start,
        timeEnd: end,
        color: _color,
        room: _roomCtrl.text.trim(),
      ),
    );
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _roomCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.course == null ? '添加课程' : '编辑课程'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _nameCtrl,
              autofocus: true,
              decoration: const InputDecoration(
                hintText: '课程名，如：高等数学',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              initialValue: _weekday,
              decoration: const InputDecoration(
                labelText: '星期',
                border: OutlineInputBorder(),
              ),
              items: List.generate(
                7,
                (i) => DropdownMenuItem(value: i, child: Text(_dayNames[i])),
              ),
              onChanged: (v) {
                Fx.tap();
                if (v != null) setState(() => _weekday = v);
              },
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _TimeBtn(
                    label: _start == null ? '开始' : _fmt(_start),
                    onTap: () => _pick(true),
                    onClear: _start == null
                        ? null
                        : () => setState(() => _start = null),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _TimeBtn(
                    label: _end == null ? '结束' : _fmt(_end),
                    onTap: () => _pick(false),
                    onClear: _end == null
                        ? null
                        : () => setState(() => _end = null),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _roomCtrl,
              decoration: const InputDecoration(
                hintText: '教室（选填）',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 14),
            const Text('颜色', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: taskColors
                  .map((c) => ChoiceChip(
                        label: Text(c.$2),
                        selected: _color == c.$1,
                        selectedColor:
                            colorFromHex(c.$1).withValues(alpha: 0.25),
                        onSelected: (_) {
                          Fx.tap();
                          setState(() => _color = c.$1);
                        },
                      ))
                  .toList(),
            ),
          ],
        ),
      ),
      actions: [
        if (widget.course != null)
          TextButton(
            onPressed: () => Navigator.pop(context, 'delete'),
            child: const Text('删除', style: TextStyle(color: Color(0xFFE53935))),
          ),
        TextButton(
          onPressed: () {
            Fx.tap();
            Navigator.pop(context);
          },
          child: const Text('取消'),
        ),
        FilledButton(
          onPressed: () {
            Fx.tap();
            _save();
          },
          child: const Text('保存'),
        ),
      ],
    );
  }
}

class _TimeBtn extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final VoidCallback? onClear;

  const _TimeBtn({
    required this.label,
    required this.onTap,
    this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        decoration: BoxDecoration(
          color: T.t.bg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: T.t.borderSoft),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.schedule, size: 16, color: T.t.text),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                  color: T.t.text, fontWeight: FontWeight.w600),
            ),
            if (onClear != null) ...[
              const SizedBox(width: 4),
              InkWell(
                onTap: onClear,
                child: Icon(Icons.close, size: 14, color: T.t.hint),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
