# experiments/

Har bir o‘qitish tajribasi alohida katalogda saqlanadi (`ai/configs/*.yaml` dagi `output_dir`):

```
experiments/<arxitektura>/
  history.csv            # har bir epoch: train/val loss, accuracy, macro F1, QWK, sinflar bo‘yicha recall, vaqt
  training_curves.png    # loss va validation metrikalari grafiklari
  train_summary.json     # eng yaxshi epoch, validation balli, o‘qitish davomiyligi, qurilma
  best.pt                # validation macro F1 bo‘yicha eng yaxshi checkpoint (git’ga qo‘shilmaydi)
  eval_test.json         # yakuniy test metrikalari (accuracy, balanced acc, P/R/F1, QWK, CM, KL0–KL2 tahlili)
  confusion_test.png     # confusion matrix grafigi
experiments/model_comparison.json   # validation bo‘yicha modellar reytingi
experiments/benchmark.json          # inference tezligi
```

**Hozirgi holat:** real dataset (OAI) bilan o‘qitish hali bajarilmagan — bu katalogda haqiqiy model
natijalari yo‘q. Faqat inference tezligi o‘lchovi mavjud: [`benchmark.md`](benchmark.md).
