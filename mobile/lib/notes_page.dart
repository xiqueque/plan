import 'package:flutter/material.dart';

import 'fx.dart';
import 'models.dart';
import 'theme.dart';

/// 便签：随手记，输入即自动保存。
class NotesPage extends StatefulWidget {
  final PlanData data;
  final VoidCallback onChanged;

  const NotesPage({super.key, required this.data, required this.onChanged});

  @override
  State<NotesPage> createState() => _NotesPageState();
}

class _NotesPageState extends State<NotesPage> {
  late final TextEditingController _ctrl;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.data.notes);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _onChanged(String value) {
    widget.data.notes = value;
    widget.onChanged();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: T.t.bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text('便签',
            style: TextStyle(fontWeight: FontWeight.bold, color: T.t.text)),
        leading: IconButton(
          icon: Icon(Icons.arrow_back, color: T.t.text),
          onPressed: () {
            Fx.tap();
            Navigator.pop(context);
          },
        ),
        actions: [
          Padding(
            padding: EdgeInsets.only(right: 16),
            child: Center(
              child: Text('自动保存',
                  style: TextStyle(fontSize: 12, color: T.t.hint)),
            ),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
        child: Container(
          decoration: BoxDecoration(
            color: T.t.card,
            borderRadius: BorderRadius.circular(18),
          ),
          child: TextField(
            controller: _ctrl,
            onChanged: _onChanged,
            maxLines: null,
            expands: true,
            textAlignVertical: TextAlignVertical.top,
            style: TextStyle(fontSize: 16, height: 1.7, color: T.t.text),
            decoration: InputDecoration(
              hintText: '随手记点什么…\n（输入自动保存）',
              hintStyle: TextStyle(color: T.t.hint),
              border: InputBorder.none,
              contentPadding:
                  const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
          ),
        ),
      ),
    );
  }
}
