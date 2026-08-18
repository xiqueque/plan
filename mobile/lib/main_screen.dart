import 'package:flutter/material.dart';

import 'fx.dart';
import 'models.dart';
import 'storage.dart';
import 'task_dialog.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  PlanData _data = PlanData();
  DateTime _date = DateTime.now();
  String _query = '';
  bool _loaded = false;

  static const _weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final d = await Storage.load();
    if (!mounted) return;
    setState(() {
      _data = d;
      _loaded = true;
    });
  }

  Future<void> _save() => Storage.save(_data);

  String _dateStr(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-'
      '${d.month.toString().padLeft(2, '0')}-'
      '${d.day.toString().padLeft(2, '0')}';

  bool get _isToday {
    final now = DateTime.now();
    return now.year == _date.year &&
        now.month == _date.month &&
        now.day == _date.day;
  }

  void _shiftDay(int delta) {
    Fx.tap();
    setState(() {
      _date = _date.add(Duration(days: delta));
    });
  }

  void _goToday() {
    Fx.tap();
    setState(() => _date = DateTime.now());
  }

  Future<void> _openTaskDialog([Task? task]) async {
    Fx.tap();
    final result = await showDialog<Task>(
      context: context,
      builder: (_) => TaskDialog(task: task, date: _date),
    );
    if (result == null) return;
    setState(() {
      if (task == null) {
        _data.tasks.add(result);
      } else {
        final idx = _data.tasks.indexWhere((t) => t.id == task.id);
        if (idx >= 0) {
          _data.tasks[idx] = result;
        }
      }
    });
    await _save();
  }

  Future<void> _toggleDone(Task t, bool value) async {
    final ds = _dateStr(_date);
    if (value) {
      final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('确认完成？'),
          content: const Text('你确定完成任务了吗( •̀ ω •́ )✧'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('我再想想¯\\_(ツ)_/¯'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('确定(●\'◡\'●)'),
            ),
          ],
        ),
      );
      if (ok != true) return;
      setState(() => _data.setDone(t.id, ds, true));
      await _save();
      Fx.complete();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('终于完成任务了耶o(*≧▽≦)ツ┏━┓！！！')),
      );
    } else {
      Fx.tap();
      setState(() => _data.setDone(t.id, ds, false));
      await _save();
    }
  }

  Future<void> _showTaskMenu(Task t) async {
    final action = await showModalBottomSheet<String>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: Icon(t.pinned ? Icons.push_pin_outlined : Icons.push_pin),
              title: Text(t.pinned ? '取消置顶' : '置顶'),
              onTap: () {
                Fx.tap();
                Navigator.pop(ctx, 'pin');
              },
            ),
            ListTile(
              leading: const Icon(Icons.edit_outlined),
              title: const Text('编辑'),
              onTap: () {
                Fx.tap();
                Navigator.pop(ctx, 'edit');
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete_outline, color: Colors.red),
              title: const Text('删除', style: TextStyle(color: Colors.red)),
              onTap: () {
                Fx.tap();
                Navigator.pop(ctx, 'delete');
              },
            ),
          ],
        ),
      ),
    );
    switch (action) {
      case 'pin':
        setState(() {
          t.pinned = !t.pinned;
          t.pinnedAt = DateTime.now().millisecondsSinceEpoch / 1000;
        });
        await _save();
      case 'edit':
        await _openTaskDialog(t);
      case 'delete':
        await _deleteTask(t);
    }
  }

  Future<void> _deleteTask(Task t) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除计划'),
        content: Text('确定删除「${t.text}」吗？'),
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
      _data.tasks.removeWhere((x) => x.id == t.id);
      _data.done.forEach((_, m) => m.remove(t.id));
    });
    await _save();
  }

  @override
  Widget build(BuildContext context) {
    if (!_loaded) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }
    final ds = _dateStr(_date);
    final tasks = _data.tasksForDate(ds).where((t) {
      if (_query.isEmpty) return true;
      return t.text.contains(_query);
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFFEAF6FC),
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildSearch(),
            Expanded(
              child: tasks.isEmpty
                  ? _buildEmpty()
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(16, 4, 16, 100),
                      itemCount: tasks.length,
                      itemBuilder: (_, i) => _buildTaskTile(tasks[i], ds),
                    ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openTaskDialog(),
        backgroundColor: const Color(0xFF7FB8D4),
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        child: const Icon(Icons.add, size: 30),
      ),
    );
  }

  Widget _buildHeader() {
    final now = DateTime.now();
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 12, 8, 4),
      child: Row(
        children: [
          IconButton(
            onPressed: () => _shiftDay(-1),
            icon: const Icon(Icons.chevron_left, size: 32),
            color: const Color(0xFF1F3A4D),
          ),
          Expanded(
            child: Column(
              children: [
                Text(
                  '${_date.month}月${_date.day}日 ${_weekdayNames[_date.weekday - 1]}',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F3A4D),
                  ),
                ),
                if (!_isToday)
                  TextButton(
                    onPressed: _goToday,
                    style: TextButton.styleFrom(
                      minimumSize: const Size(0, 30),
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                    ),
                    child: Text(
                      '回到今天 ${now.month}月${now.day}日',
                      style: const TextStyle(
                          fontSize: 13, color: Color(0xFF6B8CA3)),
                    ),
                  )
                else
                  const SizedBox(height: 8),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _shiftDay(1),
            icon: const Icon(Icons.chevron_right, size: 32),
            color: const Color(0xFF1F3A4D),
          ),
        ],
      ),
    );
  }

  Widget _buildSearch() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
      child: TextField(
        onChanged: (v) => setState(() => _query = v.trim()),
        decoration: InputDecoration(
          hintText: '搜索计划…',
          prefixIcon: const Icon(Icons.search, color: Color(0xFF6B8CA3)),
          suffixIcon: _query.isEmpty
              ? null
              : IconButton(
                  icon: const Icon(Icons.clear, color: Color(0xFF6B8CA3)),
                  onPressed: () => setState(() => _query = ''),
                ),
          filled: true,
          fillColor: Colors.white,
          contentPadding: const EdgeInsets.symmetric(vertical: 2),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(16),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Text('📋', style: TextStyle(fontSize: 56)),
          const SizedBox(height: 12),
          Text(
            _query.isEmpty ? '今天还没有计划~\n点右下角 + 添加一条吧' : '没有找到相关计划',
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Color(0xFF6B8CA3),
              fontSize: 15,
              height: 1.6,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTaskTile(Task t, String ds) {
    final done = _data.isDone(t.id, ds);
    final color = done ? const Color(0xFF9AA9B3) : colorFromHex(t.color);
    final timeText = formatTimePeriod(t.timeStart, t.timeEnd);
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => _openTaskDialog(t),
        onLongPress: () => _showTaskMenu(t),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          child: Row(
            children: [
              _CheckCircle(
                done: done,
                color: colorFromHex(t.color),
                onTap: () => _toggleDone(t, !done),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t.text,
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.bold,
                        color: color,
                        decoration: done ? TextDecoration.lineThrough : null,
                        decorationColor: color,
                      ),
                    ),
                    if (timeText.isNotEmpty) ...[
                      const SizedBox(height: 3),
                      Text(
                        timeText,
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF8A9BA8),
                        ),
                      ),
                    ],
                    if (t.isDaily) ...[
                      const SizedBox(height: 3),
                      const Text(
                        '每天重复',
                        style: TextStyle(
                          fontSize: 11,
                          color: Color(0xFF7FB8D4),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (t.pinned) ...[
                const Icon(Icons.push_pin, size: 18, color: Color(0xFFF5A623)),
                const SizedBox(width: 4),
              ],
              IconButton(
                icon: const Icon(Icons.more_vert,
                    size: 20, color: Color(0xFF8A9BA8)),
                onPressed: () => _showTaskMenu(t),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CheckCircle extends StatelessWidget {
  final bool done;
  final Color color;
  final VoidCallback onTap;

  const _CheckCircle({
    required this.done,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        width: 34,
        height: 34,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: done ? color : Colors.white,
          border: Border.all(
            color: done ? color : const Color(0xFFA8D8EA),
            width: 2,
          ),
        ),
        child: done
            ? const Icon(Icons.check, size: 22, color: Colors.white)
            : null,
      ),
    );
  }
}
