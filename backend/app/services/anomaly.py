"""
Anomaly Detection Service
==========================
Orchestrates VestoraAnomalyDetector used by daily pipeline."""
   all_flags = []
   for symbol in symbols:
       flags = await run_anomaly_detection(db, symbol, exchange)
       all_flags.extend(flags)
   return {
       "total_flags": len(all_flags),
       "exchange":    exchange,
       "flags":       all_flags,
   }


async def _store_flag(db: AsyncSession, flag: Dict) -> None:
   """Persist anomaly flag to DB. Skip duplicates."""
   from sqlalchemy import select
   existing = await db.execute(
       select(AnomalyFlagModel).where(
           AnomalyFlagModel.symbol   == flag["symbol"],
           AnomalyFlagModel.date     == flag.get("date"),
           AnomalyFlagModel.anomaly_type == flag["anomaly_type"],
       )
   )
   if existing.scalar_one_or_none():
       return  # already stored

   row = AnomalyFlagModel(
       symbol        = flag["symbol"],
       exchange      = flag.get("exchange", "NSE"),
       date          = flag.get("date"),
       anomaly_type  = flag["anomaly_type"],
       anomaly_score = flag["anomaly_score"],
       description   = flag["description"],
   )
   db.add(row)
   await db.commit()