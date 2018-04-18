from data import logger


def test_unwrap_exception_message() -> None:
    try:
        try:
            raise ZeroDivisionError('ZeroDivisionError Message')
        except ZeroDivisionError as exc:
            raise ValueError('ValueError Message') from exc
    except ValueError as exc:
        assert logger.unwrap_exception_message(exc, ' - ') == 'ValueError Message - ZeroDivisionError Message'
