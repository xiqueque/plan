import 'package:flutter/material.dart';

import 'app_theme.dart';
import 'fx.dart';
import 'models.dart';
import 'sync_page.dart';
import 'theme.dart';

/// 设置页：主题选择 + 音效/震动开关。
class SettingsPage extends StatefulWidget {
  final PlanData data;
  final VoidCallback onChanged;

  const SettingsPage({super.key, required this.data, required this.onChanged});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  late String _themeId;
  late bool _sound;
  late bool _vibrate;

  @override
  void initState() {
    super.initState();
    final s = widget.data.settings;
    _themeId = (s['theme'] as String?) ?? appThemeDefault.id;
    _sound = s['sound'] != false;
    _vibrate = s['vibrate'] != false;
    T.notifier.addListener(_onTheme);
  }

  @override
  void dispose() {
    T.notifier.removeListener(_onTheme);
    super.dispose();
  }

  void _onTheme() {
    if (mounted) setState(() {});
  }

  void _persist() {
    widget.data.settings['theme'] = _themeId;
    widget.data.settings['sound'] = _sound;
    widget.data.settings['vibrate'] = _vibrate;
    Fx.soundEnabled = _sound;
    Fx.vibrationEnabled = _vibrate;
    widget.onChanged();
  }

  void _pickTheme(String id) {
    Fx.tap();
    setState(() => _themeId = id);
    T.apply(id);
    _persist();
  }

  Future<void> _openSync() async {
    Fx.tap();
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => SyncPage(data: widget.data, onChanged: widget.onChanged),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final allThemes = <String, AppTheme>{appThemeDefault.id: appThemeDefault}
      ..addAll(appThemes);
    return Scaffold(
      backgroundColor: T.t.bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('设置',
            style: TextStyle(fontWeight: FontWeight.bold, color: T.t.text)),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: T.t.text),
          onPressed: () {
            Fx.tap();
            Navigator.pop(context);
          },
        ),
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 32),
        children: [
          Text('主题',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: T.t.text)),
          const SizedBox(height: 10),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            mainAxisSpacing: 10,
            crossAxisSpacing: 10,
            childAspectRatio: 1.45,
            children: allThemes.entries
                .map((e) => _ThemeCard(
                      theme: e.value,
                      selected: e.key == _themeId,
                      onTap: () => _pickTheme(e.key),
                    ))
                .toList(),
          ),
          const SizedBox(height: 24),
          Text('反馈',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: T.t.text)),
          const SizedBox(height: 6),
          Container(
            decoration: BoxDecoration(
              color: T.t.card,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                SwitchListTile(
                  title: Text('按键音效', style: TextStyle(color: T.t.text)),
                  subtitle: Text('点击按钮时的可爱小音效',
                      style: TextStyle(color: T.t.hint, fontSize: 12)),
                  value: _sound,
                  onChanged: (v) {
                    Fx.tap();
                    setState(() => _sound = v);
                    _persist();
                  },
                ),
                const Divider(height: 1, indent: 16, endIndent: 16),
                SwitchListTile(
                  title: Text('按键震动', style: TextStyle(color: T.t.text)),
                  subtitle: Text('点击按钮时轻微震动',
                      style: TextStyle(color: T.t.hint, fontSize: 12)),
                  value: _vibrate,
                  onChanged: (v) {
                    Fx.tap();
                    setState(() => _vibrate = v);
                    _persist();
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),
          Text('数据',
              style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                  color: T.t.text)),
          const SizedBox(height: 6),
          Container(
            decoration: BoxDecoration(
              color: T.t.card,
              borderRadius: BorderRadius.circular(16),
            ),
            child: ListTile(
              onTap: _openSync,
              leading: Icon(Icons.sync, color: T.t.primary),
              title: Text('电脑同步（同一 WiFi）',
                  style: TextStyle(color: T.t.text)),
              subtitle: Text('拉取或推送电脑上的计划数据',
                  style: TextStyle(color: T.t.hint, fontSize: 12)),
              trailing: Icon(Icons.chevron_right, color: T.t.hint),
            ),
          ),
        ],
      ),
    );
  }
}

class _ThemeCard extends StatelessWidget {
  final AppTheme theme;
  final bool selected;
  final VoidCallback onTap;

  const _ThemeCard({
    required this.theme,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: theme.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? theme.primary : theme.borderSoft,
            width: selected ? 2.5 : 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Container(
                width: double.infinity,
                decoration: BoxDecoration(
                  color: theme.bg,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        color: theme.primary,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        color: theme.button,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        color: theme.text,
                        shape: BoxShape.circle,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: Text(
                    theme.id,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: theme.text,
                      fontSize: 14,
                    ),
                  ),
                ),
                if (selected)
                  Icon(Icons.check_circle, size: 16, color: theme.primary),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
