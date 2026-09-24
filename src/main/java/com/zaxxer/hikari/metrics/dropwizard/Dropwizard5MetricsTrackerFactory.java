/*
 * Copyright (C) 2013, 2014 Brett Wooldridge
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.zaxxer.hikari.metrics.dropwizard;

import com.zaxxer.hikari.metrics.IMetricsTracker;
import com.zaxxer.hikari.metrics.MetricsTrackerFactory;
import com.zaxxer.hikari.metrics.PoolStats;
import io.dropwizard.metrics5.MetricRegistry;

public class Dropwizard5MetricsTrackerFactory implements MetricsTrackerFactory
{
   private final MetricRegistry registry;

   public Dropwizard5MetricsTrackerFactory(final MetricRegistry registry)
   {
      this.registry = registry;
   }

   public MetricRegistry getRegistry()
   {
      return registry;
   }

   @Override
   public IMetricsTracker create(final String poolName, final PoolStats poolStats)
   {
      return new Dropwizard5MetricsTracker(poolName, poolStats, registry);
   }
}
