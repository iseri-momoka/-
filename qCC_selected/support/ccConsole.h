#pragma once
// SLIM: Minimal ccConsole replacement - maps to ccLog
#include <ccLog.h>

class ccConsole
{
public:
	static void Print(const QString& message) { ccLog::Print(message); }
	static void Warning(const QString& message) { ccLog::Warning(message); }
	static void Error(const QString& message) { ccLog::Error(message); }
};
