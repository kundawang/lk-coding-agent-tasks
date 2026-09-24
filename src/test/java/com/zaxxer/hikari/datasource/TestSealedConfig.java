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

package com.zaxxer.hikari.datasource;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import com.zaxxer.hikari.util.Credentials;
import org.junit.Test;

import java.sql.Connection;
import java.sql.SQLException;

import static com.zaxxer.hikari.pool.TestElf.newHikariConfig;
import static org.junit.Assert.fail;

public class TestSealedConfig
{
   @Test(expected = IllegalStateException.class)
   public void testSealed1() throws SQLException
   {
      HikariConfig config = newHikariConfig();
      config.setDataSourceClassName("com.zaxxer.hikari.mocks.StubDataSource");

      try (HikariDataSource ds = new HikariDataSource(config)) {
         ds.setDataSourceClassName("com.zaxxer.hikari.mocks.StubDataSource");
         fail("Exception should have been thrown");
      }
   }

   @Test(expected = IllegalStateException.class)
   public void testSealed2() throws SQLException
   {
      HikariDataSource ds = new HikariDataSource();
      ds.setDataSourceClassName("com.zaxxer.hikari.mocks.StubDataSource");

      try (HikariDataSource closeable = ds) {
         try (Connection connection = ds.getConnection()) {
            ds.setDataSourceClassName("com.zaxxer.hikari.mocks.StubDataSource");
            fail("Exception should have been thrown");
         }
      }
   }

   @Test(expected = IllegalStateException.class)
   public void testSealed3() throws SQLException
   {
      HikariDataSource ds = new HikariDataSource();
      ds.setDataSourceClassName("com.zaxxer.hikari.mocks.StubDataSource");

      try (HikariDataSource closeable = ds) {
         try (Connection connection = ds.getConnection()) {
            ds.setAutoCommit(false);
            fail("Exception should have been thrown");
         }
      }
   }

   @Test
   public void testSealedAccessibleMethods() throws SQLException
   {
      HikariConfig config = newHikariConfig();
      config.setDataSourceClassName("com.zaxxer.hikari.mocks.StubDataSource");

      try (HikariDataSource ds = new HikariDataSource(config)) {
         ds.setConnectionTimeout(5000);
         ds.setValidationTimeout(5000);
         ds.setIdleTimeout(30000);
         ds.setLeakDetectionThreshold(60000);
         ds.setMaxLifetime(1800000);
         ds.setMinimumIdle(5);
         ds.setMaximumPoolSize(8);
         ds.setPassword("password");
         ds.setUsername("username");
         ds.setCredentials(Credentials.of("anothername", "anotherpassword"));
      }
   }
}
