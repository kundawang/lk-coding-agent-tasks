/*
 * Copyright (c) 2007 Mockito contributors
 * This program is made available under the terms of the MIT License.
 */
package org.mockito.internal;

import java.util.Collections;
import java.util.List;
import org.mockito.MockedConstruction;
import org.mockito.plugins.MockMaker;

public final class MockedConstructionImpl<T>
        extends ScopedMockImpl<MockMaker.ConstructionMockControl<T>>
        implements MockedConstruction<T> {

    protected MockedConstructionImpl(MockMaker.ConstructionMockControl<T> control) {
        super(control);
    }

    @Override
    public List<T> constructed() {
        return Collections.unmodifiableList(control.getMocks());
    }
}
