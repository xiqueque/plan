import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/services.dart';

/// 按键交互反馈：可爱小音效 + 轻微震动（仿电脑版）。
class Fx {
  Fx._();

  /// 是否播放按键音效 / 震动（由设置控制）
  static bool soundEnabled = true;
  static bool vibrationEnabled = true;

  static final AudioPlayer _clickPlayer = AudioPlayer();
  static final AudioPlayer _donePlayer = AudioPlayer();
  static bool _init = false;

  static Future<void> _ensure() async {
    if (_init) return;
    _init = true;
    await _clickPlayer.setReleaseMode(ReleaseMode.stop);
    await _clickPlayer.setVolume(0.15);
    await _donePlayer.setReleaseMode(ReleaseMode.stop);
    await _donePlayer.setVolume(0.15);
  }

  /// 普通按键：轻震 + 可爱小音效
  static Future<void> tap() async {
    try {
      if (vibrationEnabled) {
        await HapticFeedback.lightImpact();
      }
      if (!soundEnabled) return;
      await _ensure();
      await _clickPlayer.stop();
      await _clickPlayer.play(AssetSource('sounds/click.wav'));
    } catch (_) {
      // 音效/震动失败不影响使用
    }
  }

  /// 完成任务：略强一点的震动 + 完成音效
  static Future<void> complete() async {
    try {
      if (vibrationEnabled) {
        await HapticFeedback.mediumImpact();
      }
      if (!soundEnabled) return;
      await _ensure();
      await _donePlayer.stop();
      await _donePlayer.play(AssetSource('sounds/done.wav'));
    } catch (_) {
      // 音效/震动失败不影响使用
    }
  }
}
