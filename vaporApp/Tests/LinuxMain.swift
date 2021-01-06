import XCTest

import devTests

var tests = [XCTestCaseEntry]()
tests += devTests.allTests()
XCTMain(tests)
