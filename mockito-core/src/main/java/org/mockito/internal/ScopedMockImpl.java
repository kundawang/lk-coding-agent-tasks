/*
 * Copyright (c) 2026 Mockito contributors
 * This program is made available under the terms of the MIT License.
 */
package org.mockito.internal;

import org.mockito.ScopedMock;
import org.mockito.exceptions.base.MockitoException;
import org.mockito.internal.debugging.LocationFactory;
import org.mockito.invocation.Location;
import org.mockito.plugins.MockMaker.ScopedMockControl;

import static org.mockito.internal.util.StringUtil.join;

public class ScopedMockImpl<T extends ScopedMockControl> implements ScopedMock {

    protected final T control;

    private final Location location = LocationFactory.create();

    private boolean closed;

    public ScopedMockImpl(T control) {
        this.control = control;
    }

    @Override
    public boolean isClosed() {
        return closed;
    }

    @Override
    public void close() {
        assertNotClosed();

        closed = true;
        control.disable();
    }

    @Override
    public void closeOnDemand() {
        if (!closed) {
            close();
        }
    }

    protected void assertNotClosed() {
        if (closed) {
            throw new MockitoException(
                    join(
                            "The scoped mock created at",
                            location.toString(),
                            "is already resolved and cannot longer be used"));
        }
    }
}
