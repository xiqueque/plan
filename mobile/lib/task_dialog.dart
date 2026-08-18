import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'fx.dart';
import 'image_store.dart';
import 'models.dart';

class TaskDialog extends StatefulWidget {
  final Task? task;
  final DateTime date;
  final PlanData? data;

  const TaskDialog({super.key, this.task, required this.date, this.data});

  @override
  State<TaskDialog> createState() => _TaskDialogState();
}

class _TaskDialogState extends State<TaskDialog> {
  late final TextEditingController _textCtrl;
  late String _color;
  late bool _isDaily;
  late bool _reminderOn;
  late String _reminderMode; // once=当天提醒, daily=每天提醒
  TimeOfDay? _reminderTime;
  late Set<int> _reminderWeekdays; // 0=周一 … 6=周日
  late List<String> _images;
  TimeOfDay? _start;
  TimeOfDay? _end;

  @override
  void initState() {
    super.initState();
    final t = widget.task;
    _textCtrl = TextEditingController(text: t?.text ?? '');
    _color = t?.color ?? '#1F3A4D';
    _isDaily = t?.isDaily ?? false;
    _reminderOn = (t?.reminderMode ?? 'none') != 'none';
    _reminderMode = t?.reminderMode == 'daily' ? 'daily' : 'once';
    _reminderTime = _parseTime(t?.reminderTime);
    _reminderWeekdays = (t?.reminderWeekdays ?? List.generate(7, (i) => i))
        .toSet();
    _images = List.of(t?.images ?? []);
    _start = _parseTime(t?.timeStart);
    _end = _parseTime(t?.timeEnd);
  }

  TimeOfDay? _parseTime(String? s) {
    if (s == null || !s.contains(':')) return null;
    final parts = s.split(':');
    return TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
  }

  String _fmt(TimeOfDay? t) => t == null
      ? ''
      : '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  Future<void> _pickTime(bool isStart) async {
    Fx.tap();
    final picked = await showTimePicker(
      context: context,
      initialTime: isStart
          ? (_start ?? const TimeOfDay(hour: 9, minute: 0))
          : (_end ?? const TimeOfDay(hour: 10, minute: 0)),
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

  Future<void> _pickReminderTime() async {
    Fx.tap();
    final picked = await showTimePicker(
      context: context,
      initialTime:
          _reminderTime ?? _start ?? const TimeOfDay(hour: 9, minute: 0),
    );
    if (picked != null) {
      setState(() => _reminderTime = picked);
    }
  }

  Future<void> _pickImage() async {
    Fx.tap();
    try {
      final picked = await ImagePicker()
          .pickImage(source: ImageSource.gallery, maxWidth: 2000);
      if (picked == null) return;
      final name = await ImageStore.import(File(picked.path));
      if (!mounted) return;
      setState(() => _images.add(name));
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('选择图片失败，请检查相册权限')),
        );
      }
    }
  }

  Future<void> _removeImage(String name) async {
    Fx.tap();
    final data = widget.data;
    final referencedElsewhere = data != null &&
        data.tasks.any((t) => t.id != widget.task?.id && t.images.contains(name));
    if (!referencedElsewhere) {
      await ImageStore.delete(name);
    }
    setState(() => _images.remove(name));
  }

  @override
  void dispose() {
    _textCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.task == null ? '添加计划' : '编辑计划'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _textCtrl,
              autofocus: true,
              maxLines: 3,
              minLines: 1,
              decoration: const InputDecoration(
                hintText: '写点什么…',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                _TimeButton(
                  label: _start == null ? '开始时间' : _fmt(_start),
                  onTap: () => _pickTime(true),
                  onClear: _start == null
                      ? null
                      : () => setState(() => _start = null),
                ),
                const SizedBox(width: 10),
                _TimeButton(
                  label: _end == null ? '结束时间' : _fmt(_end),
                  onTap: () => _pickTime(false),
                  onClear:
                      _end == null ? null : () => setState(() => _end = null),
                ),
              ],
            ),
            const SizedBox(height: 14),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('到点提醒'),
              subtitle: Text(_reminderOn
                  ? (_reminderMode == 'daily' ? '每天提醒' : '当天提醒')
                  : '关闭'),
              value: _reminderOn,
              onChanged: (v) {
                Fx.tap();
                setState(() {
                  _reminderOn = v;
                  if (v) {
                    _reminderMode = _isDaily ? 'daily' : 'once';
                    _reminderTime ??= _start ?? const TimeOfDay(hour: 9, minute: 0);
                  }
                });
              },
            ),
            if (_reminderOn) ...[
              const SizedBox(height: 4),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'once', label: Text('当天提醒')),
                  ButtonSegment(value: 'daily', label: Text('每天提醒')),
                ],
                selected: {_reminderMode},
                showSelectedIcon: false,
                style: const ButtonStyle(
                  visualDensity: VisualDensity.compact,
                ),
                onSelectionChanged: (s) {
                  Fx.tap();
                  setState(() {
                    _reminderMode = s.first;
                    if (_reminderMode == 'daily') {
                      _isDaily = true;
                      if (_reminderWeekdays.isEmpty) {
                        _reminderWeekdays = {0, 1, 2, 3, 4, 5, 6};
                      }
                    }
                  });
                },
              ),
              const SizedBox(height: 10),
              _TimeButton(
                label: _reminderTime == null ? '提醒时间' : _fmt(_reminderTime),
                onTap: _pickReminderTime,
                onClear: _reminderTime == null
                    ? null
                    : () => setState(() => _reminderTime = null),
              ),
              if (_reminderMode == 'daily') ...[
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Text('提醒日',
                        style: TextStyle(fontWeight: FontWeight.bold)),
                    const Spacer(),
                    TextButton(
                      onPressed: () {
                        Fx.tap();
                        setState(() => _reminderWeekdays = {0, 1, 2, 3, 4, 5, 6});
                      },
                      child: const Text('全选'),
                    ),
                    TextButton(
                      onPressed: () {
                        Fx.tap();
                        setState(() => _reminderWeekdays = {0, 1, 2, 3, 4});
                      },
                      child: const Text('工作日'),
                    ),
                  ],
                ),
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: List.generate(7, (i) => _WeekdayChip(
                        index: i,
                        selected: _reminderWeekdays.contains(i),
                        onTap: () {
                          Fx.tap();
                          setState(() {
                            if (_reminderWeekdays.contains(i)) {
                              _reminderWeekdays.remove(i);
                            } else {
                              _reminderWeekdays.add(i);
                            }
                          });
                        },
                      )),
                ),
              ],
            ],
            const SizedBox(height: 14),
            const Text('颜色', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: taskColors
                  .map((c) => _ColorChip(
                        hex: c.$1,
                        label: c.$2,
                        selected: _color == c.$1,
                        onTap: () {
                          Fx.tap();
                          setState(() => _color = c.$1);
                        },
                      ))
                  .toList(),
            ),
            const SizedBox(height: 8),
            SwitchListTile(
              contentPadding: EdgeInsets.zero,
              title: const Text('每天重复'),
              subtitle: const Text('每天自动出现在计划里'),
              value: _isDaily,
              onChanged: (v) {
                Fx.tap();
                setState(() {
                  _isDaily = v;
                  if (v) {
                    _reminderOn = true;
                    _reminderMode = 'daily';
                    if (_reminderWeekdays.isEmpty) {
                      _reminderWeekdays = {0, 1, 2, 3, 4, 5, 6};
                    }
                  } else if (_reminderMode == 'daily') {
                    _reminderMode = 'once';
                  }
                });
              },
            ),
            const SizedBox(height: 14),
            const Text('图片', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ..._images.map((name) => _ImageThumb(
                      name: name,
                      onRemove: () => _removeImage(name),
                    )),
                _AddImageTile(onTap: _pickImage),
              ],
            ),
          ],
        ),
      ),
      actions: [
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

  void _save() {
    final text = _textCtrl.text.trim();
    if (text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('写点内容再保存吧~')),
      );
      return;
    }
    final old = widget.task;
    final start = _fmt(_start);
    final end = _fmt(_end);
    final reminderTime = _fmt(_reminderTime);
    final task = Task(
      id: old?.id ?? newTaskId(),
      text: text,
      date: old?.date ??
          '${widget.date.year.toString().padLeft(4, '0')}-'
              '${widget.date.month.toString().padLeft(2, '0')}-'
              '${widget.date.day.toString().padLeft(2, '0')}',
      timeStart: start.isEmpty ? null : start,
      timeEnd: end.isEmpty ? null : end,
      isDaily: _isDaily || (_reminderOn && _reminderMode == 'daily'),
      color: _color,
      reminderMode: _reminderOn ? _reminderMode : 'none',
      reminderTime: _reminderOn && reminderTime.isNotEmpty ? reminderTime : null,
      reminderWeekdays: _reminderWeekdays.toList()..sort(),
      images: _images,
      pinned: old?.pinned ?? false,
      pinnedAt: old?.pinnedAt,
      createdAt: old?.createdAt ?? DateTime.now().millisecondsSinceEpoch / 1000,
    );
    Navigator.pop(context, task);
  }
}

class _TimeButton extends StatelessWidget {
  final String label;
  final VoidCallback onTap;
  final VoidCallback? onClear;

  const _TimeButton({
    required this.label,
    required this.onTap,
    this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: const Color(0xFFEAF6FC),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFA8D8EA)),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.schedule, size: 18, color: Color(0xFF1F3A4D)),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  label,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      color: Color(0xFF1F3A4D), fontWeight: FontWeight.w600),
                ),
              ),
              if (onClear != null) ...[
                const SizedBox(width: 4),
                InkWell(
                  onTap: onClear,
                  child: const Icon(Icons.close,
                      size: 16, color: Color(0xFF8A9BA8)),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _ColorChip extends StatelessWidget {
  final String hex;
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _ColorChip({
    required this.hex,
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final c = colorFromHex(hex);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: selected ? c.withValues(alpha: 0.2) : Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: selected ? c : const Color(0xFFD5E8F2),
            width: selected ? 2 : 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 14,
              height: 14,
              decoration: BoxDecoration(color: c, shape: BoxShape.circle),
            ),
            const SizedBox(width: 6),
            Text(
              label,
              style: TextStyle(
                color: Color(0xFF1F3A4D),
                fontWeight: selected ? FontWeight.bold : FontWeight.normal,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _WeekdayChip extends StatelessWidget {
  final int index; // 0=周一 … 6=周日
  final bool selected;
  final VoidCallback onTap;

  const _WeekdayChip({
    required this.index,
    required this.selected,
    required this.onTap,
  });

  static const _names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        width: 42,
        height: 34,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: selected ? const Color(0xFF7FB8D4) : Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: selected ? const Color(0xFF7FB8D4) : const Color(0xFFD5E8F2),
          ),
        ),
        child: Text(
          _names[index],
          style: TextStyle(
            fontSize: 12,
            color: selected ? Colors.white : const Color(0xFF1F3A4D),
            fontWeight: selected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }
}

class _ImageThumb extends StatelessWidget {
  final String name;
  final VoidCallback onRemove;

  const _ImageThumb({required this.name, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<File?>(
      future: ImageStore.file(name),
      builder: (_, snap) {
        final f = snap.data;
        return Stack(
          children: [
            Container(
              width: 76,
              height: 76,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                color: const Color(0xFFEAF6FC),
              ),
              clipBehavior: Clip.antiAlias,
              child: f == null
                  ? const Center(
                      child: Icon(Icons.image, color: Color(0xFFA8D8EA)))
                  : Image.file(
                      f,
                      width: 76,
                      height: 76,
                      fit: BoxFit.cover,
                    ),
            ),
            Positioned(
              top: -4,
              right: -4,
              child: GestureDetector(
                onTap: onRemove,
                child: Container(
                  padding: const EdgeInsets.all(4),
                  decoration: const BoxDecoration(
                    color: Color(0xFFE53935),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.close,
                      size: 14, color: Colors.white),
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _AddImageTile extends StatelessWidget {
  final VoidCallback onTap;

  const _AddImageTile({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 76,
        height: 76,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
              color: const Color(0xFFA8D8EA), width: 1.5),
          color: Colors.white,
        ),
        child: const Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.add_photo_alternate_outlined,
                size: 24, color: Color(0xFF7FB8D4)),
            SizedBox(height: 2),
            Text('添加图片',
                style: TextStyle(fontSize: 10, color: Color(0xFF6B8CA3))),
          ],
        ),
      ),
    );
  }
}
