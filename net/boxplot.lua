done = function(summary, latency, requests)
   print("--- Boxplot Stats ---")
   print(string.format("lower whisker (Min): %g ms", latency.min / 1000.0))
   print(string.format("lower quartile (25%%): %g ms", latency:percentile(25.0) / 1000.0))
   print(string.format("median (50%%): %g ms", latency:percentile(50.0) / 1000.0))
   print(string.format("upper quartile (75%%): %g ms", latency:percentile(75.0) / 1000.0))
   print(string.format("upper whisker (Max): %g ms", latency.max / 1000.0))
   print(string.format("average: %g ms", latency.mean / 1000.0))
end
