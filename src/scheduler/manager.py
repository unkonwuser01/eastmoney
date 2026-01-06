from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from typing import Dict
from src.storage.db import get_active_funds, get_fund_by_code
from src.analysis.pre_market import PreMarketAnalyst
from src.analysis.post_market import PostMarketAnalyst
from src.report_gen import save_report

logger = logging.getLogger(__name__)

class SchedulerManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchedulerManager, cls).__new__(cls)
            cls._instance.scheduler = BackgroundScheduler()
            cls._instance.scheduler.start()
        return cls._instance

    def start(self):
        """Load jobs from DB and start"""
        print("Starting Scheduler Manager...")
        self.refresh_all_jobs()
        
    def refresh_all_jobs(self):
        """Clear all and reload from DB"""
        self.scheduler.remove_all_jobs()
        funds = get_active_funds()
        for fund in funds:
            self.add_fund_jobs(fund)

    def add_fund_jobs(self, fund: Dict):
        """Add Pre/Post market jobs for a single fund"""
        code = fund['code']
        
        # Pre-market
        if fund.get('pre_market_time'):
            try:
                hour, minute = fund['pre_market_time'].split(':')
                job_id = f"pre_{code}"
                self.scheduler.add_job(
                    self.run_analysis_task,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    id=job_id,
                    args=[code, 'pre'],
                    replace_existing=True
                )
                print(f"Scheduled PRE-market for {code} at {hour}:{minute}")
            except Exception as e:
                print(f"Error scheduling PRE task for {code}: {e}")

        # Post-market
        if fund.get('post_market_time'):
            try:
                hour, minute = fund['post_market_time'].split(':')
                job_id = f"post_{code}"
                self.scheduler.add_job(
                    self.run_analysis_task,
                    trigger=CronTrigger(hour=hour, minute=minute),
                    id=job_id,
                    args=[code, 'post'],
                    replace_existing=True
                )
                print(f"Scheduled POST-market for {code} at {hour}:{minute}")
            except Exception as e:
                print(f"Error scheduling POST task for {code}: {e}")

    def remove_fund_jobs(self, code: str):
        """Remove jobs for a fund"""
        for mode in ['pre', 'post']:
            job_id = f"{mode}_{code}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                print(f"Removed job {job_id}")

    def run_analysis_task(self, fund_code: str, mode: str):
        """Worker function"""
        print(f"Executing {mode.upper()}-market task for {fund_code}...")
        
        # Re-fetch fund data to ensure latest config
        fund = get_fund_by_code(fund_code)
        if not fund or not fund['is_active']:
            print(f"Fund {fund_code} is inactive or deleted. Skipping.")
            return

        report = ""
        try:
            if mode == 'pre':
                analyst = PreMarketAnalyst()
                report = analyst.analyze_fund(fund)
            elif mode == 'post':
                analyst = PostMarketAnalyst()
                report = analyst.analyze_fund(fund)
            
            if report:
                # Need to implement file naming logic in save_report to handle individual funds
                save_report(report, mode, fund['name'], fund['code'])
                
        except Exception as e:
            logger.error(f"Task failed for {fund_code}: {e}")
            print(f"Task failed for {fund_code}: {e}")

# Global instance
scheduler_manager = SchedulerManager()
