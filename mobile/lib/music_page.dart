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

  static final _platforms = [
    _Platform(
      '网易云音乐',
      const _LogoNetease(),
      'orpheus://search/',
      'https://music.163.com/#/search/m/?s=',
    ),
    _Platform(
      'QQ音乐',
      const _LogoQQ(),
      'qqmusic://search?key=',
      'https://y.qq.com/n/ryqq/search?w=',
    ),
    _Platform(
      '酷狗音乐',
      const _LogoKugou(),
      'kugou://search/keyword=',
      'https://www.kugou.com/yy/html/search.html'
          '#searchType=song&searchKeyWord=',
    ),
    _Platform(
      '哔哩哔哩',
      const _LogoBili(),
      'bilibili://search/',
      'https://search.bilibili.com/all?keyword=',
    ),
    _Platform(
      '抖音',
      const _LogoDouyin(),
      'snssdk1128://search?keyword=',
      'https://www.douyin.com/search/',
    ),
  ];

  Future<void> _open(_Platform p) async {
    final q = _query.trim();
    if (q.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('先输入想找的歌曲名吧')),
      );
      return;
    }
    Fx.tap();
    final encoded = Uri.encodeComponent(q);
    // 优先用 App 专属协议直跳，失败再退回网页（浏览器打开）
    final schemeUri = Uri.parse('${p.scheme}$encoded');
    try {
      if (await canLaunchUrl(schemeUri)) {
        await launchUrl(schemeUri, mode: LaunchMode.externalApplication);
        return;
      }
    } catch (_) {
      // 继续尝试网页
    }
    try {
      final webUri = Uri.parse('${p.web}$encoded');
      final ok =
          await launchUrl(webUri, mode: LaunchMode.externalApplication);
      if (!ok && mounted) {
        _hint('打开失败，请检查 ${p.name} 是否安装');
      }
    } catch (_) {
      if (mounted) {
        _hint('打开失败，请稍后再试');
      }
    }
  }

  void _hint(String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
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
            textInputAction: TextInputAction.search,
            decoration: InputDecoration(
              hintText: '搜歌名，如：红色高跟鞋',
              prefixIcon: Icon(Icons.search, color: T.t.hint),
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
  final Widget logo;
  final String scheme;
  final String web;

  const _Platform(this.name, this.logo, this.scheme, this.web);
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
        leading: SizedBox(width: 42, height: 42, child: platform.logo),
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

/// 各品牌真实配色的 Logo（简化版，保证一眼认出）。
class _LogoNetease extends StatelessWidget {
  const _LogoNetease();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFD33A31),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(Icons.music_note, color: Colors.white, size: 26),
    );
  }
}

class _LogoQQ extends StatelessWidget {
  const _LogoQQ();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF31C27C),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(Icons.music_note, color: Colors.white, size: 26),
    );
  }
}

class _LogoKugou extends StatelessWidget {
  const _LogoKugou();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF2C9BFF),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(Icons.music_note, color: Colors.white, size: 26),
    );
  }
}

class _LogoBili extends StatelessWidget {
  const _LogoBili();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFB7299),
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(Icons.tv, color: Colors.white, size: 24),
    );
  }
}

class _LogoDouyin extends StatelessWidget {
  const _LogoDouyin();

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF161823),
        borderRadius: BorderRadius.circular(10),
      ),
      child: ShaderMask(
        shaderCallback: (rect) => const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF25F4EE), Color(0xFFFE2C55)],
        ).createShader(rect),
        child: const Icon(Icons.music_note, color: Colors.white, size: 26),
      ),
    );
  }
}
