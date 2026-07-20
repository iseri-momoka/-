// ##########################################################################
// #                                                                        #
// #                   CLOUDCOMPARE LIGHT VIEWER                            #
// #                                                                        #
// #  This project has been initiated under funding from ANR/CIFRE          #
// #                                                                        #
// #  This program is free software; you can redistribute it and/or modify  #
// #  it under the terms of the GNU General Public License as published by  #
// #  the Free Software Foundation; version 2 or later of the License.      #
// #                                                                        #
// #  This program is distributed in the hope that it will be useful,       #
// #  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
// #  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          #
// #  GNU General Public License for more details.                          #
// #                                                                        #
// #      +++ COPYRIGHT: EDF R&D + TELECOM ParisTech (ENST-TSI) +++         #
// #                                                                        #
// ##########################################################################

#ifndef CCVIEWER_LOG_HEADER
#define CCVIEWER_LOG_HEADER

// Qt
#include <QCoreApplication>
#include <QDateTime>
#include <QDir>
#include <QFile>
#include <QMainWindow>
#include <QMessageBox>
#include <QTextStream>

// qCC_db
#include <ccLog.h>

//! Logger for ccViewer: displays error dialogs and writes all messages to a log file
class ccViewerLog : public ccLog
{
  public:
	//! Default constructor
	explicit ccViewerLog(QMainWindow* parentWindow = nullptr)
	    : ccLog()
	    , m_parentWindow(parentWindow)
	{
		s_instance = this;

		// Create logs directory under the application directory
		QDir logsDir(QCoreApplication::applicationDirPath() + "/logs");
		if (!logsDir.exists())
		{
			logsDir.mkpath(".");
		}

		// Generate log file name with timestamp
		QString timestamp = QDateTime::currentDateTime().toString("yyyyMMdd_HHmmss");
		QString logFilePath = logsDir.filePath("ccViewer_" + timestamp + ".log");

		m_logFile.setFileName(logFilePath);
		if (m_logFile.open(QIODevice::WriteOnly | QIODevice::Text))
		{
			m_logStream.setDevice(&m_logFile);
			// Qt6 defaults to UTF-8; no need for setCodec()

			// Write header
			m_logStream << "=== ccViewer Log Started: "
			            << QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
			            << " ===" << Qt::endl;
		}
	}

	//! Destructor — flush and close log file
	~ccViewerLog() override
	{
		if (m_logFile.isOpen())
		{
			m_logStream << "=== ccViewer Log Ended: "
			            << QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
			            << " ===" << Qt::endl;
			m_logFile.close();
		}
	}

	//! Returns the static logger instance (for use by other classes like ccViewer)
	[[nodiscard]] static ccViewerLog* instance()
	{
		return s_instance;
	}

	//! Returns the current log file path (empty if no file is open)
	[[nodiscard]] QString logFilePath() const
	{
		return m_logFile.fileName();
	}

	//! Write a message to the log file (can be called externally from dispToConsole)
	void writeToFile(const QString& message, int level)
	{
		if (!m_logFile.isOpen())
		{
			return;
		}

		m_logStream << QDateTime::currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
		            << " [" << levelPrefix(level) << "] "
		            << message << Qt::endl;
		m_logStream.flush();
	}

  protected:
	// inherited from ccLog
	void logMessage(const QString& message, int level) override
	{
		// Original behavior: show error dialog for errors
		if (level & LOG_ERROR)
		{
			if (m_parentWindow)
			{
				QMessageBox::warning(m_parentWindow, "Error", message);
			}
		}

		// Write all messages to log file
		writeToFile(message, level);
	}

  private:
	//! Returns a short prefix for the given log level
	static const char* levelPrefix(int level)
	{
		int baseLevel = level & 7; // strip debug flag
		switch (baseLevel)
		{
		case LOG_VERBOSE:
			return "V";
		case LOG_STANDARD:
			return "S";
		case LOG_IMPORTANT:
			return "I";
		case LOG_WARNING:
			return "W";
		case LOG_ERROR:
			return "E";
		default:
			return "?";
		}
	}

	//! Associated window
	QMainWindow* m_parentWindow;

	//! Log file
	QFile m_logFile;

	//! Log text stream
	QTextStream m_logStream;

	//! Static instance pointer (for access from ccViewer)
	inline static ccViewerLog* s_instance = nullptr;
};

#endif // CCVIEWER_LOG_HEADER
