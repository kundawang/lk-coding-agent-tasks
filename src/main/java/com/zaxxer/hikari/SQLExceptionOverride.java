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

package com.zaxxer.hikari;

import java.sql.SQLException;

/**
 * Users can implement this interface to override the default SQLException handling
 * of HikariCP. When a SQLException is thrown from JDBC execution methods, the
 * SQLState and error code will be checked to determine if the connection should
 * be evicted from the pool.
 * <p>
 * By supplying an implementation of this interface, users can override the default
 * handling of SQLExceptions. The {@link #adjudicate(SQLException)} method will be called
 * with the SQLException that was thrown. If the method returns {@link Override#CONTINUE_EVICT}
 * the customary built-in handling will occur. If the method returns {@link Override#DO_NOT_EVICT}
 * the eviction will be elided. If the method returns {@link Override#MUST_EVICT} the eviction will
 * be evicted regardless of the SQLState or error code.
 */
public interface SQLExceptionOverride {
   enum Override {
      CONTINUE_EVICT,
      DO_NOT_EVICT,
      MUST_EVICT
   }

   /**
    * This method is called when a SQLException is thrown from a JDBC method.
    *
    * @param sqlException the SQLException that was thrown
    * @return an {@link Override} value indicating how eviction should proceed
    */
   default Override adjudicate(final SQLException sqlException)
   {
      return Override.CONTINUE_EVICT;
   }
}
