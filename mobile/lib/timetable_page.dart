import 'package:flutter/material.dart';

import 'fx.dart';
import 'models.dart';
import 'theme.dart';

/// 课表：自行设置一周七天的课程。
class TimetablePage extends StatefulWidget {
  final PlanData data;
  final VoidCallback onChanged;

  const TimetablePage({super.key, required this.data, required this.onChanged});

  @override
  State<TimetablePage> createState() => _TimetablePageState();
}

class _TimetablePageState extends State<TimetablePage> {
  static const _dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  List<Course> _coursesOf(int weekday) {
    final list = widget.data.timetable
        .where((c) => c.weekday == weekday)
        .toList()
      ..sort((a, b) => a.timeStart.compareTo(b.timeStart));
    return list;
  }

  Future<void> _openCourseDialog([Course? course]) async {
    final result = await showDialog<Object>(
      context: context,
      builder: (_) => CourseDialog(course: course),
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
        final idx =
            widget.data.timetable.indexWhere((c) => c.id == course.id);
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
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 32),
        children: [
          for (var d = 0; d < 7; d++) ...[
            Padding(
              padding: const EdgeInsets.only(top: 10, bottom: 6),
              child: Row(
                children: [
                  Text(
                    _dayNames[d],
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: T.t.text,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _coursesOf(d).isEmpty ? '' : '${_coursesOf(d).length} 节',
                    style: TextStyle(fontSize: 12, color: T.t.hint),
                  ),
                ],
              ),
            ),
            if (_coursesOf(d).isEmpty)
              Container(
                margin: const EdgeInsets.only(bottom: 4),
                padding: const EdgeInsets.symmetric(vertical: 12),
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: T.t.card,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text('这天没课',
                    style: TextStyle(fontSize: 13, color: T.t.hint)),
              )
            else
              ..._coursesOf(d).map((c) => _buildCourseTile(c)),
          ],
        ],
      ),
    );
  }

  Widget _buildCourseTile(Course c) {
    final color = colorFromHex(c.color);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: T.t.card,
        borderRadius: BorderRadius.circular(14),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(14),
        onTap: () => _openCourseDialog(c),
        onLongPress: () => _deleteCourse(c),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            children: [
              Container(
                width: 5,
                height: 38,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      c.name,
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: T.t.text,
                      ),
                    ),
                    if (c.room.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        c.room,
                        style: TextStyle(fontSize: 12, color: T.t.hint),
                      ),
                    ],
                  ],
                ),
              ),
              Text(
                '${c.timeStart} – ${c.timeEnd}',
                style: TextStyle(fontSize: 13, color: T.t.hint),
              ),
              IconButton(
                icon: const Icon(Icons.delete_outline,
                    size: 18, color: Color(0xFFE53935)),
                onPressed: () => _deleteCourse(c),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class CourseDialog extends StatefulWidget {
  final Course? course;

  const CourseDialog({super.key, this.course});

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
    _weekday = c?.weekday ?? 0;
    _color = c?.color ?? '#1F3A4D';
    _start = _parse(c?.timeStart);
    _end = _parse(c?.timeEnd);
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
