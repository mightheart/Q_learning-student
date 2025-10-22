"""Performance monitoring utility for stress testing."""

import time
import psutil
import os


def monitor_performance(duration_seconds: int = 60) -> None:
    """Monitor CPU and memory usage of the running simulation.
    
    Args:
        duration_seconds: How long to monitor (default 60 seconds)
    """
    
    print(f"Monitoring performance for {duration_seconds} seconds...")
    print("Looking for python.exe process running simulation...")
    
    # Find the simulation process
    target_process = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and 'main.py' in ' '.join(cmdline):
                    target_process = psutil.Process(proc.info['pid'])
                    print(f"Found process: PID {proc.info['pid']}")
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not target_process:
        print("❌ Could not find simulation process!")
        print("Please start the simulation first: python src/main.py")
        return
    
    print("\n" + "="*60)
    print("Performance Monitoring Started")
    print("="*60)
    print(f"{'Time':<10} {'CPU %':<10} {'Memory MB':<12} {'Status':<20}")
    print("-"*60)
    
    start_time = time.time()
    samples = []
    
    try:
        while time.time() - start_time < duration_seconds:
            try:
                cpu_percent = target_process.cpu_percent(interval=1.0)
                memory_mb = target_process.memory_info().rss / 1024 / 1024
                
                elapsed = int(time.time() - start_time)
                status = "Running"
                
                print(f"{elapsed:<10} {cpu_percent:<10.2f} {memory_mb:<12.2f} {status:<20}")
                
                samples.append({
                    'time': elapsed,
                    'cpu': cpu_percent,
                    'memory': memory_mb
                })
                
            except psutil.NoSuchProcess:
                print("⚠️  Process terminated")
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Monitoring stopped by user")
    
    # Print summary
    if samples:
        print("\n" + "="*60)
        print("Performance Summary")
        print("="*60)
        
        avg_cpu = sum(s['cpu'] for s in samples) / len(samples)
        max_cpu = max(s['cpu'] for s in samples)
        avg_memory = sum(s['memory'] for s in samples) / len(samples)
        max_memory = max(s['memory'] for s in samples)
        
        print(f"Average CPU:    {avg_cpu:.2f}%")
        print(f"Peak CPU:       {max_cpu:.2f}%")
        print(f"Average Memory: {avg_memory:.2f} MB")
        print(f"Peak Memory:    {max_memory:.2f} MB")
        print(f"Samples taken:  {len(samples)}")
        
        # Performance rating
        print("\n" + "="*60)
        print("Performance Rating")
        print("="*60)
        
        if avg_cpu < 30 and max_memory < 300:
            print("✅ Excellent - System running smoothly!")
        elif avg_cpu < 50 and max_memory < 500:
            print("✅ Good - Acceptable performance")
        elif avg_cpu < 70 and max_memory < 800:
            print("⚠️  Fair - May experience slowdowns")
        else:
            print("❌ Poor - Optimization recommended")


if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("❌ psutil not installed!")
        print("Install it with: pip install psutil")
        exit(1)
    
    print("Campus Simulation - Performance Monitor")
    print("="*60)
    print("This tool monitors CPU and memory usage of the simulation.")
    print("Make sure the simulation is running before starting monitor.")
    print("="*60)
    
    input("Press ENTER to start monitoring (or Ctrl+C to cancel)...")
    
    monitor_performance(duration_seconds=120)  # Monitor for 2 minutes
