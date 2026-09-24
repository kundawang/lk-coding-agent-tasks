/*
 * Copyright (c) 2007 Mockito contributors
 * This program is made available under the terms of the MIT License.
 */
package org.mockito.internal;

import org.mockito.MockedSingleton;
import org.mockito.plugins.MockMaker;

public final class MockedSingletonImpl<T> extends ScopedMockImpl<MockMaker.SingletonMockControl<T>>
        implements MockedSingleton<T> {

    public MockedSingletonImpl(MockMaker.SingletonMockControl<T> control) {
        super(control);
    }

    @Override
    public T getInstance() {
        return control.getInstance();
    }

    @Override
    public String toString() {
        return "singleton mock for " + control.getInstance();
    }
}
