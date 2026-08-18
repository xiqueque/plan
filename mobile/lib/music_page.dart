import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'fx.dart';
import 'theme.dart';

/// 音乐：搜索歌名后跳转到手机上的音乐 App 打开（版权归原平台）。
class MusicPage extends StatefulWidget {
  const MusicPage({super.key});

  @override
  State<MusicPage> createState() => _MusicPageState();
}

class _MusicPageState extends State<MusicPage> {
  final TextEditingController _ctrl = TextEditingController();
  String _query = '';

  static const _platforms = [
    _Platform('网易云音乐', '🎵', Color(0xFFD33A31), _urlNetease),
    _Platform('QQ音乐', '🐧', Color(0xFF31C27C), _urlQQ),
    _Platform('酷狗音乐', '🎤', Color(0xFF2C9BFF), _urlKugou),
    _Platform('哔哩哔哩', '📺', Color(0xFFFB7299), _urlBili),
    _Platform('抖音', '🎬', Color(0xFF161823), _urlDouyin),
  ];

  static String _urlNetease(String q) =>
      'https://music.163.com/#/search/m/?s=${Uri.encodeComponent(q)}';
  static String _urlQQ(String q) =>
      'https://y.qq.com/n/ryqq/search?w=${Uri.encodeComponent(q)}';
  static String _urlKugou(String q) =>
      'https://www.kugou.com/yy/html/search.html'
      '#searchType=song&searchKeyWord=${Uri.encodeComponent(q)}';
  static String _urlBili(String q) =>
      'https://search.bilibili.com/all?keyword=${Uri.encodeComponent(q)}';
  static String _urlDouyin(String q) =>
      'https://www.douyin.com/search/${Uri.encodeComponent(q)}';

  Future<void> _open(_Platform p) async {
    final q = _query.trim();
    if (q.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('先输入想找的歌曲名吧')),
      );
      return;
    }
    Fx.tap();
    try {
      final ok = await launchUrl(
        Uri.parse(p.url(q)),
        mode: LaunchMode.externalApplication,
      );
      if (!ok && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('没有找到可打开的 App，试试浏览器')),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('打开失败，请稍后再试')),
        );
      }
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: T.t.bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('音乐',
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
          TextField(
            controller: _ctrl,
            onChanged: (v) => setState(() => _query = v),
            onSubmitted: (_) {},
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: '搜歌名，如：红色高跟鞋',
              prefixIcon: Icon(Icons.search, color: T.t.hint),
              suffixIcon: IconButton(
                icon: Icon(Icons.arrow_forward, color: T.t.primary),
                onPressed: () {},
              ),
              filled: true,
              fillColor: T.t.card,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: BorderSide.none,
              ),
            ),
          ),
          const SizedBox(height: 18),
          Text('选择打开方式',
              style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: T.t.text)),
          const SizedBox(height: 4),
          Text('搜索后会跳到对应 App 里播放，歌曲版权归各平台所有。',
              style: TextStyle(fontSize: 12, color: T.t.hint)),
          const SizedBox(height: 10),
          ..._platforms.map((p) => _PlatformTile(
                platform: p,
                query: _query,
                onTap: () => _open(p),
              )),
          const SizedBox(height: 20),
          Text('小提示：如果手机上没装某个 App，会改为用浏览器打开搜索结果。',
              style: TextStyle(fontSize: 12, color: T.t.hint)),
        ],
      ),
    );
  }
}

class _Platform {
  final String name;
  final String emoji;
  final Color color;
  final String Function(String) url;

  const _Platform(this.name, this.emoji, this.color, this.url);
}

class _PlatformTile extends StatelessWidget {
  final _Platform platform;
  final String query;
  final VoidCallback onTap;

  const _PlatformTile({
    required this.platform,
    required this.query,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final q = query.trim();
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: T.t.card,
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListTile(
        onTap: onTap,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        leading: Container(
          width: 40,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: platform.color,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Text(platform.emoji, style: const TextStyle(fontSize: 20)),
        ),
        title: Text(
          platform.name,
          style: TextStyle(
              fontWeight: FontWeight.bold, color: T.t.text),
        ),
        subtitle: Text(
          q.isEmpty ? '在 ${platform.name} 中搜索' : '搜索「$q」',
          style: TextStyle(fontSize: 12, color: T.t.hint),
        ),
        trailing: Icon(Icons.open_in_new, size: 18, color: T.t.hint),
      ),
    );
  }
}
