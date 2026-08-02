from skills.tests.mock_services import create_mock_context


context = create_mock_context()


print("Logger:", context.logger)

print("System:", context.system)

print("Input:", context.input)

print("Files:", context.files)

print("Browser:", context.browser)

print("Vision:", context.vision)