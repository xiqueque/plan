import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'app_theme.dart';
import 'fx.dart';
import 'models.dart';
import 'reminder_service.dart';
import 'theme.dart';

/// 把电脑端数据应用到本地（保留手机本地设置与同步地址）。
void applyRemoteData(PlanData local, Map<String, dynamic> remoteJson) {
  final remote = PlanData.fromJson(remoteJson);
  final theme = local.settings['theme'];
  final sound = local.settings['sound'];
  final vibrate = local.settings['vibrate'];
  final ip = local.settings['sync_ip'];
  final port = local.settings['sync_port'];
  local.settings = remote.settings;
  local.settings['theme'] = theme ?? appThemeDefault.id;
  local.settings['sound'] = sound ?? true;
  local.settings['vibrate'] = vibrate ?? true;
  if (ip != null) local.settings['sync_ip'] = ip;
  if (port != null) local.settings['sync_port'] = port;
  local.tasks = remote.tasks;
  local.timetable = remote.timetable;
  local.done = remote.done;
  local.reminded = remote.reminded;
  local.dayImages = remote.dayImages;
  local.imageNames = remote.imageNames;
  local.imageDaily = remote.imageDaily;
  local.notes = remote.notes;
}

/// 同步页：同一 WiFi 下与电脑互相拉取/推送数据。
class SyncPage extends StatefulWidget {
  final PlanData data;
  final VoidCallback onChanged;

  const SyncPage({super.key, required this.data, required this.onChanged});

  @override
  State<SyncPage> createState() => _SyncPageState();
}

class _SyncPageState extends State<SyncPage> {
  late final TextEditingController _ipCtrl;
  late final TextEditingController _portCtrl;
  bool _busy = false;
  String _status = '';

  @override
  void initState() {
    super.initState();
    _ipCtrl = TextEditingController(
        text: (widget.data.settings['sync_ip'] as String?) ?? '');
    _portCtrl = TextEditingController(
        text: (widget.data.settings['sync_port'] as String?) ?? '47520');
  }

  @override
  void dispose() {
    _ipCtrl.dispose();
    _portCtrl.dispose();
    super.dispose();
  }

  String get _baseUrl {
    var ip = _ipCtrl.text.trim();
    var port = _portCtrl.text.trim();
    if (port.isEmpty) port = '47520';
    return 'http://$ip:$port';
  }

  void _saveAddr() {
    widget.data.settings['sync_ip'] = _ipCtrl.text.trim();
    widget.data.settings['sync_port'] = _portCtrl.text.trim();
    widget.onChanged();
  }

  Future<void> _pull() async {
    Fx.tap();
    final url = _baseUrl;
    setState(() {
      _busy = true;
      _status = '正在连接电脑…';
    });
    try {
      final resp = await http
          .get(Uri.parse('$url/api/plan'))
          .timeout(const Duration(seconds: 8));
      if (resp.statusCode != 200) {
        throw Exception('电脑返回错误（${resp.statusCode}）');
      }
      final remote =
          jsonDecode(utf8.decode(resp.bodyBytes)) as Map<String, dynamic>;
      applyRemoteData(widget.data, remote);
      await ReminderService.instance.rescheduleAll(widget.data);
      _saveAddr();
      if (!mounted) return;
      setState(() =>
          _status = '✓ 已从电脑拉取数据（${widget.data.tasks.length} 条计划）');
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = '✗ 拉取失败：$e\n'
          '请确认：电脑已启动同步服务、手机和电脑在同一 WiFi');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _push() async {
    Fx.tap();
    final url = _baseUrl;
    setState(() {
      _busy = true;
      _status = '正在推送手机数据…';
    });
    try {
      final resp = await http
          .post(
            Uri.parse('$url/api/plan'),
            headers: {'Content-Type': 'application/json; charset=utf-8'},
            body: jsonEncode(widget.data.toJson()),
          )
          .timeout(const Duration(seconds: 8));
      if (resp.statusCode != 200) {
        throw Exception('电脑返回错误（${resp.statusCode}）');
      }
      final body = jsonDecode(utf8.decode(resp.bodyBytes));
      _saveAddr();
      if (!mounted) return;
      setState(() => _status =
          '✓ 手机数据已推送到电脑${body is Map && body['message'] != null ? '：${body['message']}' : ''}');
    } catch (e) {
      if (!mounted) return;
      setState(() => _status = '✗ 推送失败：$e\n'
          '请确认：电脑已启动同步服务、手机和电脑在同一 WiFi');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: T.t.bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('同步',
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
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: T.t.card,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('使用步骤',
                    style: TextStyle(
                        fontWeight: FontWeight.bold, color: T.t.text)),
                SizedBox(height: 6),
                Text(
                  '1. 电脑打开「每日计划」→ 点底部「🔄 同步」，看到"运行中"；\n'
                  '2. 手机和电脑连同一个 WiFi；\n'
                  '3. 在下面输入电脑上显示的 IP 地址；\n'
                  '4. 点「拉取」把电脑数据拿到手机，点「推送」把手机数据发给电脑。',
                  style: TextStyle(fontSize: 13, color: T.t.hint, height: 1.7),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _ipCtrl,
            keyboardType: TextInputType.url,
            decoration: InputDecoration(
              labelText: '电脑 IP 地址',
              hintText: '如 192.168.1.100',
              prefixIcon: Icon(Icons.computer, color: T.t.hint),
              filled: true,
              fillColor: T.t.card,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide.none,
              ),
            ),
          ),
          const SizedBox(height: 10),
          TextField(
            controller: _portCtrl,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(
              labelText: '端口',
              hintText: '47520',
              filled: true,
              fillColor: T.t.card,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(14),
                borderSide: BorderSide.none,
              ),
            ),
          ),
          const SizedBox(height: 18),
          FilledButton.icon(
            onPressed: _busy ? null : _pull,
            style: FilledButton.styleFrom(
              backgroundColor: T.t.primary,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            icon: const Icon(Icons.download),
            label: const Text('拉取：电脑 → 手机',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: _busy ? null : _push,
            style: FilledButton.styleFrom(
              backgroundColor: T.t.button,
              foregroundColor: T.t.text,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            icon: const Icon(Icons.upload),
            label: const Text('推送：手机 → 电脑',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
          ),
          const SizedBox(height: 16),
          Text(
            _status,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 13, color: T.t.text, height: 1.6),
          ),
          const SizedBox(height: 8),
          Text(
            '提示：同步内容包含计划、课表、便签和完成状态；图片文件暂不随数据同步。'
            '手机推送到电脑前，电脑会自动备份旧数据。',
            style: TextStyle(fontSize: 12, color: T.t.hint, height: 1.6),
          ),
        ],
      ),
    );
  }
}
