# experiments/

Har bir o‘qitish tajribasi alohida katalogda saqlanadi (`ai/configs/*.yaml` dagi `output_dir`):

```
experiments/<arxitektura>/
  history.csv            # har bir epoch: train/val loss, accuracy, balanced acc, macro P/R/F1, QWK, recall, vaqt
  val_metrics.json       # eng yaxshi epochdagi validation metrikalari
  eval_val.json, confusion_val.png
  training_curves.png    # loss va validation metrikalari grafiklari
  train_summary.json     # eng yaxshi epoch, validation balli, o‘qitish davomiyligi, qurilma
  best.pt                # validation macro F1 bo‘yicha eng yaxshi checkpoint (git’ga qo‘shilmaydi)
  eval_test.json         # yakuniy test metrikalari (accuracy, balanced acc, P/R/F1, QWK, CM, KL0–KL2 tahlili)
  confusion_test.png     # confusion matrix grafigi
experiments/model_comparison.json/.md  # validation bo‘yicha modellar reytingi va tanlov sababi
experiments/test_lock.json          # test to‘plami qaysi (yagona) checkpoint uchun ishlatilgani
experiments/EXPERIMENT_REPORT.md    # make_report.py — faqat yuqoridagi fayllardan yig‘ilgan hisobot
experiments/benchmark.json          # inference tezligi
```

**Hozirgi holat:** real dataset (OAI) bilan o‘qitish hali bajarilmagan — bu katalogda haqiqiy model
natijalari yo‘q. Faqat inference tezligi o‘lchovi mavjud: [`benchmark.md`](benchmark.md).
