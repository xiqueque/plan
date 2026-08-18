import 'package:flutter/material.dart';

import 'fx.dart';
import 'models.dart';
import 'reminder_service.dart';
import 'storage.dart';
import 'task_dialog.dart';

/// 日历：月份网格 + 选中日期的任务预览 + 跳转到某一天。
class CalendarPage extends StatefulWidget {
  final DateTime initial;
  final PlanData data;

  const CalendarPage({super.key, required this.initial, required this.data});

  @override
  State<CalendarPage> createState() => _CalendarPageState();
}

class _CalendarPageState extends State<CalendarPage> {
  static const _weekNames = ['一', '二', '三', '四', '五', '六', '日'];
  static const _dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  late DateTime _month;
  late DateTime _selected;

  @override
  void initState() {
    super.initState();
    _selected = widget.initial;
    _month = DateTime(_selected.year, _selected.month);
  }

  String _dateStr(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  void _shiftMonth(int delta) {
    Fx.tap();
    setState(() => _month = DateTime(_month.year, _month.month + delta));
  }

  void _goToday() {
    Fx.tap();
    setState(() {
      final now = DateTime.now();
      _month = DateTime(now.year, now.month);
      _selected = now;
    });
  }

  Future<void> _editTask(Task task) async {
    final result = await showDialog<Task>(
      context: context,
      builder: (_) => TaskDialog(task: task, date: _selected, data: widget.data),
    );
    if (result == null) return;
    setState(() {
      final idx = widget.data.tasks.indexWhere((t) => t.id == task.id);
      if (idx >= 0) {
        widget.data.tasks[idx] = result;
      }
    });
    await Storage.save(widget.data);
    await ReminderService.instance.scheduleForTask(result);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEAF6FC),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('日历',
            style: TextStyle(
                color: Color(0xFF1F3A4D), fontWeight: FontWeight.bold)),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Color(0xFF1F3A4D)),
          onPressed: () {
            Fx.tap();
            Navigator.pop(context);
          },
        ),
        actions: [
          TextButton(
            onPressed: _goToday,
            child: const Text('今天', style: TextStyle(color: Color(0xFF6B8CA3))),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: _buildCalendarCard(),
          ),
          const SizedBox(height: 12),
          Expanded(child: _buildDayList()),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: () => Navigator.pop(context, _selected),
                style: FilledButton.styleFrom(
                  backgroundColor: const Color(0xFF7FB8D4),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                icon: const Icon(Icons.today),
                label: Text(
                  '跳转到 ${_selected.month}月${_selected.day}日',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCalendarCard() {
    final first = DateTime(_month.year, _month.month);
    final offset = (first.weekday - 1) % 7; // 周一开头
    final daysInMonth = DateTime(_month.year, _month.month + 1, 0).day;
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);

    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Row(
            children: [
              IconButton(
                onPressed: () => _shiftMonth(-1),
                icon: const Icon(Icons.chevron_left, color: Color(0xFF1F3A4D)),
              ),
              Expanded(
                child: Text(
                  '${_month.year}年${_month.month}月',
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F3A4D),
                  ),
                ),
              ),
              IconButton(
                onPressed: () => _shiftMonth(1),
                icon: const Icon(Icons.chevron_right, color: Color(0xFF1F3A4D)),
              ),
            ],
          ),
          Row(
            children: _weekNames
                .map((w) => Expanded(
                      child: Center(
                        child: Text(
                          w,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF8A9BA8),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ))
                .toList(),
          ),
          const SizedBox(height: 6),
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 7,
              childAspectRatio: 0.95,
            ),
            itemCount: 42,
            itemBuilder: (_, i) {
              final day = i - offset + 1;
              if (day < 1 || day > daysInMonth) {
                return const SizedBox.shrink();
              }
              final date = DateTime(_month.year, _month.month, day);
              final ds = _dateStr(date);
              final hasTasks = widget.data.tasksForDate(ds).isNotEmpty;
              final isToday = date == today;
              final isSelected = date.year == _selected.year &&
                  date.month == _selected.month &&
                  date.day == _selected.day;
              return GestureDetector(
                onTap: () {
                  Fx.tap();
                  setState(() => _selected = date);
                },
                child: Container(
                  margin: const EdgeInsets.all(2),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? const Color(0xFFB9DEEE)
                        : Colors.transparent,
                    shape: BoxShape.circle,
                    border: isToday && !isSelected
                        ? Border.all(color: const Color(0xFF7FB8D4), width: 1.5)
                        : null,
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        '$day',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight:
                              isSelected || isToday ? FontWeight.bold : FontWeight.normal,
                          color: isToday
                              ? const Color(0xFF1E88E5)
                              : const Color(0xFF1F3A4D),
                        ),
                      ),
                      const SizedBox(height: 2),
                      Container(
                        width: 5,
                        height: 5,
                        decoration: BoxDecoration(
                          color: hasTasks
                              ? const Color(0xFF7FB8D4)
                              : Colors.transparent,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildDayList() {
    final ds = _dateStr(_selected);
    final tasks = widget.data.tasksForDate(ds);
    return ListView(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      children: [
        Text(
          '${_selected.month}月${_selected.day}日 ${_dayNames[_selected.weekday - 1]}'
          '${tasks.isEmpty ? '' : ' · ${tasks.length} 条计划'}',
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1F3A4D),
          ),
        ),
        const SizedBox(height: 8),
        if (tasks.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Center(
              child: Text(
                '这一天还没有计划',
                style: TextStyle(color: Color(0xFF8A9BA8)),
              ),
            ),
          )
        else
          ...tasks.map((t) => _buildTaskTile(t, ds)),
      ],
    );
  }

  Widget _buildTaskTile(Task t, String ds) {
    final done = widget.data.isDone(t.id, ds);
    final color = done ? const Color(0xFF9AA9B3) : colorFromHex(t.color);
    final timeText = formatTimePeriod(t.timeStart, t.timeEnd);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
      ),
      child: ListTile(
        onTap: () => _editTask(t),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        leading: Icon(
          done ? Icons.check_circle : Icons.radio_button_unchecked,
          color: done ? color : const Color(0xFFA8D8EA),
        ),
        title: Text(
          t.text,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: color,
            decoration: done ? TextDecoration.lineThrough : null,
          ),
        ),
        subtitle: timeText.isEmpty
            ? null
            : Text(
                timeText,
                style: const TextStyle(fontSize: 12, color: Color(0xFF8A9BA8)),
              ),
        trailing: t.pinned
            ? const Icon(Icons.push_pin, size: 16, color: Color(0xFFF5A623))
            : null,
      ),
    );
  }
}
