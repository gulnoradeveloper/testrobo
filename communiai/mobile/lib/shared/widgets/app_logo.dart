import 'package:flutter/material.dart';

/// CommuniAI logo (assets/images/logo.png). Replace that file to update the brand everywhere.
class AppLogo extends StatelessWidget {
  const AppLogo({super.key, this.size = 96});
  final double size;
  @override
  Widget build(BuildContext context) => Image.asset(
        'assets/images/logo.png',
        width: size,
        height: size,
        fit: BoxFit.contain,
        errorBuilder: (_, _, _) => Icon(Icons.forum_rounded, size: size * 0.8, color: Colors.white),
      );
}
