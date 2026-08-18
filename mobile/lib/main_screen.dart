import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import 'calendar_page.dart';
import 'app_theme.dart';
import 'fx.dart';
import 'image_store.dart';
import 'models.dart';
import 'music_page.dart';
import 'reminder_service.dart';
import 'settings_page.dart';
import 'storage.dart';
import 'task_dialog.dart';
import 'theme.dart';
import 'timetable_page.dart';

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
  bool _showImages = false;

  static const _weekdayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];

  @override
  void initState() {
    super.initState();
    T.notifier.addListener(_onThemeChanged);
    _load();
  }

  @override
  void dispose() {
    T.notifier.removeListener(_onThemeChanged);
    super.dispose();
  }

  void _onThemeChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _load() async {
    final d = await Storage.load();
    if (!mounted) return;
    setState(() {
      _data = d;
      _loaded = true;
    });
    T.apply((d.settings['theme'] as String?) ?? appThemeDefault.id);
    Fx.soundEnabled = d.settings['sound'] != false;
    Fx.vibrationEnabled = d.settings['vibrate'] != false;
    await ReminderService.instance.init();
    await ReminderService.instance.rescheduleAll(_data);
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
      builder: (_) => TaskDialog(task: task, date: _date, data: _data),
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
    await ReminderService.instance.scheduleForTask(result);
  }

  Future<void> _openCalendar() async {
    Fx.tap();
    final picked = await Navigator.push<DateTime>(
      context,
      MaterialPageRoute(
        builder: (_) => CalendarPage(initial: _date, data: _data),
      ),
    );
    if (picked != null && mounted) {
      setState(() => _date = picked);
    }
  }

  Future<void> _openSettings() async {
    Fx.tap();
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => SettingsPage(data: _data, onChanged: () => _save()),
      ),
    );
  }

  Future<void> _openTimetable() async {
    Fx.tap();
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TimetablePage(data: _data, onChanged: () => _save()),
      ),
    );
  }

  Future<void> _openMusic() async {
    Fx.tap();
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const MusicPage()),
    );
  }

  Widget _headerShortcut(IconData icon, String label, VoidCallback onTap) {
    return TextButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 15, color: T.t.primary),
      label: Text(label,
          style: TextStyle(fontSize: 12, color: T.t.hint)),
      style: TextButton.styleFrom(
        minimumSize: const Size(0, 26),
        padding: const EdgeInsets.symmetric(horizontal: 6),
        visualDensity: VisualDensity.compact,
      ),
    );
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
    for (final img in t.images) {
      final stillUsed = _data.dayImages.values.any((l) => l.contains(img)) ||
          _data.imageDaily.containsKey(img) ||
          _data.tasks.any((x) => x.images.contains(img));
      if (!stillUsed) {
        await ImageStore.delete(img);
      }
    }
    await _save();
    await ReminderService.instance.cancelForTask(t);
  }

  List<String> _imagesForDate(String ds) {
    final result = <String>[];
    final seen = <String>{};
    for (final name in _data.dayImages[ds] ?? <String>[]) {
      if (seen.add(name)) result.add(name);
    }
    _data.imageDaily.forEach((name, flag) {
      if (flag && seen.add(name)) result.add(name);
    });
    for (final t in _data.tasksForDate(ds)) {
      for (final name in t.images) {
        if (seen.add(name)) result.add(name);
      }
    }
    return result;
  }

  Future<void> _addDayImage() async {
    Fx.tap();
    try {
      final picked = await ImagePicker()
          .pickImage(source: ImageSource.gallery, maxWidth: 2000);
      if (picked == null) return;
      final name = await ImageStore.import(File(picked.path));
      final ds = _dateStr(_date);
      (_data.dayImages[ds] ??= []).add(name);
      setState(() => _showImages = true);
      await _save();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('选择图片失败，请检查相册权限')),
        );
      }
    }
  }

  Future<void> _deleteDayImage(String name) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('删除图片'),
        content: const Text('确定删除这张图片吗？'),
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
    _data.dayImages.forEach((_, l) => l.remove(name));
    _data.imageDaily.remove(name);
    final stillUsed = _data.tasks.any((t) => t.images.contains(name));
    if (!stillUsed) {
      await ImageStore.delete(name);
    }
    setState(() {});
    await _save();
  }

  Future<void> _openImageViewer(String name) async {
    Fx.tap();
    final f = await ImageStore.file(name);
    if (f == null || !mounted) return;
    final ds = _dateStr(_date);
    final isDay = (_data.dayImages[ds] ?? []).contains(name);
    final marked = _data.imageDaily[name] == true;
    final deletable = isDay || marked;
    await showDialog<void>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => Dialog.fullscreen(
          backgroundColor: Colors.black,
          child: Stack(
            children: [
              Positioned.fill(
                child: InteractiveViewer(
                  child: Center(
                    child: Image.file(f, fit: BoxFit.contain),
                  ),
                ),
              ),
              Positioned(
                top: 32,
                left: 8,
                child: IconButton(
                  icon: const Icon(Icons.close,
                      color: Colors.white, size: 28),
                  onPressed: () {
                    Fx.tap();
                    Navigator.pop(ctx);
                  },
                ),
              ),
              if (deletable)
                Positioned(
                  bottom: 48,
                  right: 8,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      IconButton(
                        icon: Icon(
                          marked
                              ? Icons.star
                              : Icons.star_border,
                          color: marked
                              ? const Color(0xFFF5A623)
                              : Colors.white,
                          size: 28,
                        ),
                        tooltip: marked ? '取消每日图片' : '设为每日图片',
                        onPressed: () {
                          Fx.tap();
                          setDialogState(() {
                            _data.imageDaily[name] =
                                _data.imageDaily[name] != true;
                          });
                        },
                      ),
                      IconButton(
                        icon: const Icon(Icons.delete_outline,
                            color: Colors.white, size: 28),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          await _deleteDayImage(name);
                        },
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
    if (!mounted) return;
    setState(() {});
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
      backgroundColor: T.t.bg,
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            _buildSearch(),
            _buildImageArea(),
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
        backgroundColor: T.t.primary,
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
            color: T.t.text,
          ),
          Expanded(
            child: Column(
              children: [
                InkWell(
                  onTap: _openCalendar,
                  borderRadius: BorderRadius.circular(10),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 12, vertical: 4),
                    child: Text(
                      '${_date.month}月${_date.day}日 ${_weekdayNames[_date.weekday - 1]}',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: T.t.text,
                      ),
                    ),
                  ),
                ),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _headerShortcut(
                        Icons.calendar_month, '日历', _openCalendar),
                    _headerShortcut(
                        Icons.event_note, '课表', _openTimetable),
                    _headerShortcut(Icons.music_note, '音乐', _openMusic),
                  ],
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
                      style: TextStyle(
                          fontSize: 13, color: T.t.hint),
                    ),
                  )
                else
                  const SizedBox(height: 4),
              ],
            ),
          ),
          IconButton(
            onPressed: () => _shiftDay(1),
            icon: const Icon(Icons.chevron_right, size: 32),
            color: T.t.text,
          ),
          IconButton(
            onPressed: _openSettings,
            icon: const Icon(Icons.settings_outlined, size: 22),
            color: T.t.hint,
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
          prefixIcon: Icon(Icons.search, color: T.t.hint),
          suffixIcon: _query.isEmpty
              ? null
              : IconButton(
                  icon: Icon(Icons.clear, color: T.t.hint),
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

  Widget _buildImageArea() {
    final ds = _dateStr(_date);
    final names = _imagesForDate(ds);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 0),
          child: Row(
            children: [
              InkWell(
                onTap: () {
                  Fx.tap();
                  setState(() => _showImages = !_showImages);
                },
                borderRadius: BorderRadius.circular(8),
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
                  child: Row(
                    children: [
                      Icon(
                        _showImages
                            ? Icons.expand_more
                            : Icons.chevron_right,
                        size: 20,
                        color: T.t.hint,
                      ),
                      const SizedBox(width: 2),
                      Icon(Icons.photo_library_outlined,
                          size: 18, color: T.t.primary),
                      const SizedBox(width: 6),
                      Text(
                        '图片 ${names.length} 张',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: T.t.text,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const Spacer(),
              TextButton.icon(
                onPressed: _addDayImage,
                icon: const Icon(Icons.add, size: 16),
                label: const Text('添加'),
                style: TextButton.styleFrom(
                  visualDensity: VisualDensity.compact,
                  foregroundColor: T.t.hint,
                ),
              ),
            ],
          ),
        ),
        if (_showImages)
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: names.isEmpty
                ? Text(
                    '今天还没有图片，点「添加」从相册选吧',
                    style: TextStyle(fontSize: 13, color: T.t.hint),
                  )
                : GridView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    gridDelegate:
                        const SliverGridDelegateWithFixedCrossAxisCount(
                      crossAxisCount: 4,
                      mainAxisSpacing: 8,
                      crossAxisSpacing: 8,
                    ),
                    itemCount: names.length,
                    itemBuilder: (_, i) {
                      final name = names[i];
                      final marked = _data.imageDaily[name] == true;
                      return FutureBuilder<File?>(
                        future: ImageStore.file(name),
                        builder: (_, snap) {
                          final f = snap.data;
                          return GestureDetector(
                            onTap: () => _openImageViewer(name),
                            child: Stack(
                              children: [
                                Container(
                                  decoration: BoxDecoration(
                                    borderRadius: BorderRadius.circular(10),
                                    color: T.t.borderSoft,
                                  ),
                                  clipBehavior: Clip.antiAlias,
                                  child: f == null
                                      ? Icon(Icons.image,
                                          color: T.t.hint)
                                      : Image.file(
                                          f,
                                          width: double.infinity,
                                          height: double.infinity,
                                          fit: BoxFit.cover,
                                        ),
                                ),
                                if (marked)
                                  const Positioned(
                                    top: 3,
                                    left: 3,
                                    child: Icon(Icons.star,
                                        size: 16, color: Color(0xFFF5A623)),
                                  ),
                              ],
                            ),
                          );
                        },
                      );
                    },
                  ),
          ),
      ],
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
            style: TextStyle(
              color: T.t.hint,
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
                        style: TextStyle(
                          fontSize: 12,
                          color: T.t.hint,
                        ),
                      ),
                    ],
                    if (t.isDaily) ...[
                      const SizedBox(height: 3),
                      Text(
                        '每天重复',
                        style: TextStyle(
                          fontSize: 11,
                          color: T.t.primary,
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
                icon: Icon(Icons.more_vert,
                    size: 20, color: T.t.hint),
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
            color: done ? color : T.t.borderSoft,
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
