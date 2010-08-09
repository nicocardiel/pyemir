/*
 * Copyright 2008-2010 Sergio Pascual
 *
 * This file is part of PyEmir
 *
 * PyEmir is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * PyEmir is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with PyEmir.  If not, see <http://www.gnu.org/licenses/>.
 *
 */


#ifndef PYEMIR_METHOD_BASE_H
#define PYEMIR_METHOD_BASE_H

#include <vector>

namespace Numina {

typedef double ResultType;
typedef std::vector<ResultType>::iterator DataIterator;
typedef std::vector<ResultType>::iterator WeightsIterator;

class CombineMethod {
public:
  virtual ~CombineMethod() {
  }
  virtual CombineMethod* clone() const = 0;
  virtual std::pair<ResultType, ResultType> central_tendency(DataIterator begin,
      DataIterator end, WeightsIterator weights) const = 0;
};

class RejectMethod {
public:
  virtual ~RejectMethod() {
  }
  virtual void combine(DataIterator begin, DataIterator end, WeightsIterator weights,
      ResultType* results[3]) const = 0;
};

} // namespace Numina

#endif // PYEMIR_METHOD_BASE_H
