/*
 * Copyright (c) 2007 Mockito contributors
 * This program is made available under the terms of the MIT License.
 */
package org.mockito;

/**
 * Represents an active thread-local mock of a singleton instance. The mocking only affects the thread
 * on which {@link Mockito#mockSingleton(Object)} was called, and the instance only behaves as a mock on that thread.
 * The singleton mock is released when this object's {@link #close()} method is invoked. If this object is never closed,
 * the mock will remain active on the initiating thread. It is therefore recommended to create this object within a
 * try-with-resources statement.
 * <p>
 * Stubbing and verification on the instance can be done using the standard Mockito APIs.
 *
 * @see Mockito#mockSingleton(Object)
 * @param <T> The type of the singleton being mocked.
 */
public interface MockedSingleton<T> extends ScopedMock {

    /**
     * Returns the mocked singleton instance.
     */
    T getInstance();
}
