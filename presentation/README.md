# BEGOYIM — animatsion taqdimot (PPTX)

26 slayd (vazirlik versiyasi), 16:9, o‘zbek tilida, har bir slaydda ma’ruzachi uchun izoh (Speaker notes).
Elementlar slayd ochilishi bilan bosqichma-bosqich avtomatik paydo bo‘ladi, slaydlar orasida silliq o‘tish.

```bash
npm install pptxgenjs sharp react react-dom react-icons
node build_deck.js out/BEGOYIM_taqdimot.pptx ../video/out/begoyim_taqdimot_web.mp4   # video 2-slaydga joylanadi
pip install lxml
python animate.py out/BEGOYIM_taqdimot.pptx                                         # animatsiya va o‘tishlar
```

Animatsiya qoidasi: obyekt nomi `a<N>_<effekt>_...` (effekt: fade | up | left | zoom) — N-bosqichda paydo bo‘ladi.

© 2026 Bo‘ronova Gulnora Yodgorovna. Barcha huquqlar himoyalangan.
